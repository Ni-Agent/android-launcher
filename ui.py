# adb + uiautomator helper used for the manual emulator steps (TEST-ONLY, not committed).
import subprocess, re, sys, time
PKG = "com.ni.launcher.dev"
def sh(c): return subprocess.run(["adb","shell"]+c.split(" "), capture_output=True, text=True).stdout
def dump():
    for _ in range(5):
        sh("uiautomator dump /sdcard/u.xml"); x = sh("cat /sdcard/u.xml")
        if "<hierarchy" in x: return x
        time.sleep(2)
    return ""
def bounds(n): return list(map(int,re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',n).groups()))
def find(text=None, desc=None, timeout=90):
    end=time.time()+timeout
    while time.time()<end:
        x=dump()
        m=re.search(r'text="Wait"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', x)
        if m: a=list(map(int,m.groups())); sh(f"input tap {(a[0]+a[2])//2} {(a[1]+a[3])//2}"); continue
        for n in re.findall(r'<node [^>]*>', x):
            if text is not None and f'text="{text}"' not in n: continue
            if desc is not None and f'content-desc="{desc}"' not in n: continue
            b=bounds(n); return ((b[0]+b[2])//2,(b[1]+b[3])//2,b)
        time.sleep(2)
    raise SystemExit(f"not found: {text or desc}")
def tap(p): sh(f"input tap {p[0]} {p[1]}")
def longpress(p): sh(f"input swipe {p[0]} {p[1]} {p[0]} {p[1]} 2000")
def wh(): return map(int,sh("wm size").strip().split()[-1].split("x"))
def rows():
    out=[]
    for n in re.findall(r'<node [^>]*>', dump()):
        m=re.search(r'text="([^"]+)"',n)
        if m and PKG in n: b=bounds(n); out.append((b[1],m.group(1),b))
    return sorted(out)
def open_all_apps_item(app):
    w,h=wh(); sh(f"input tap {w-20} {int(h*0.4)}")
    l=find(text=app[0].upper()); sh(f"input swipe {l[0]} {l[1]} {l[0]} {l[1]+1} 400"); time.sleep(2)
    c=[bounds(n) for n in re.findall(r'<node [^>]*>', dump()) if f'text="{app}"' in n]
    c=[b for b in c if b[0] < w//2] or [find(text=app)[2]]
    b=c[-1]; return ((b[0]+b[2])//2,(b[1]+b[3])//2)
cmd=sys.argv[1]
if cmd=="addfav":
    longpress(open_all_apps_item(sys.argv[2])); tap(find(text="Add to Favorites")); tap(find(desc="Confirm")); print("added", sys.argv[2])
elif cmd=="createtag":
    longpress(open_all_apps_item(sys.argv[2])); tap(find(text="Create Tag")); find(desc="Confirm"); time.sleep(3)
    print("created:", [r[1] for r in rows()])
elif cmd=="texts": print([r[1] for r in rows()])
elif cmd=="openmanage":   # long-press home row by text, open "Manage <tag>"
    longpress(find(text=sys.argv[2])); tap(find(text=sys.argv[3])); find(desc="Confirm"); time.sleep(3)
    print("manage:", [r[1] for r in rows()])
elif cmd=="remove":
    w,h=wh(); r=[r for r in rows() if r[1]==sys.argv[2]][0]; y=(r[2][1]+r[2][3])//2
    sh(f"input swipe {w//3} {y} {w-5} {y} 1500"); time.sleep(5); print("after remove:", [r[1] for r in rows()])
elif cmd=="dragtop":
    w,h=wh(); rr=[r for r in rows() if r[1]!="Add items…"]; src=[r for r in rr if r[1]==sys.argv[2]][0]; dst=rr[0]
    sh(f"input draganddrop {w-90} {(src[2][1]+src[2][3])//2} {w-90} {dst[2][1]-20} 2500"); time.sleep(4)
    print("after drag:", [r[1] for r in rows()])
elif cmd=="confirm": tap(find(desc="Confirm")); time.sleep(3); print("confirmed")
elif cmd=="tap": tap(find(text=sys.argv[2])); print("tapped", sys.argv[2])
if cmd=="longtext":
    longpress(find(text=sys.argv[2])); print("longpressed", sys.argv[2])
elif cmd=="badge":   # open All Apps at an app and tap its tag badge chip
    p=open_all_apps_item(sys.argv[2]); longpress(p); tap(find(text=sys.argv[3])); time.sleep(3); print("rows:", [r[1] for r in rows()])
elif cmd=="key":
    sh("input keyevent "+sys.argv[2])
elif cmd=="tapdesc": tap(find(desc=sys.argv[2])); print("tapped desc", sys.argv[2])
elif cmd=="popup":   # swipe right on a home row, list texts, screenshot to argv[3], back
    w,h=wh(); p=find(text=sys.argv[2]); b=p[2]
    before=set(r[1] for r in rows())
    sh(f"input swipe {b[0]} {p[1]} {b[0]+w//2} {p[1]} 300"); time.sleep(5)
    print("popup:", [r[1] for r in rows()])
    sh(f"screencap -p /sdcard/popup.png"); subprocess.run(["adb","pull","/sdcard/popup.png",sys.argv[3]],capture_output=True)
    sh("input keyevent 4"); time.sleep(2)
