"""Hold a process lock so two desktop instances cannot overwrite one save."""
import os
import ctypes

def acquire_lock(path):
    import msvcrt
    lock=path.open('a+b')
    lock.seek(0,os.SEEK_END)
    if lock.tell()==0:lock.write(b'0');lock.flush()
    lock.seek(0)
    try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:lock.close();return None
    return lock

def main():
    from questdock.app import DATA
    import msvcrt
    DATA.parent.mkdir(parents=True,exist_ok=True)
    lock=acquire_lock(DATA.parent/'instance.lock')
    if lock is None:
        from questdock.notices import show_notice
        show_notice('QuestDock 已在运行','请点击桌面悬浮球打开任务面板。')
        return
    with lock:
        try:
            from questdock.premium import App
            App().root.mainloop()
        finally:
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)

if __name__=='__main__':main()
