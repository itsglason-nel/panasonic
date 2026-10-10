import subprocess, sys, time
import socketio
TAB = "A" * 22
for order, port in (("after", 5071), ("before", 5072)):
    p = subprocess.Popen([sys.executable, "eventlet_server.py", order, str(port)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    time.sleep(2.5)
    for transports in (["polling", "websocket"], ["websocket"]):
        got = {}
        c = socketio.Client()
        c.on("hello", lambda d, g=got: g.update(d))
        try:
            c.connect(f"http://127.0.0.1:{port}", transports=transports,
                      socketio_path=f"t/{TAB}/socket.io", wait_timeout=6)
            time.sleep(1.5)
            print(f"[eventlet, TabScope {order} init_app] {transports}: connected, "
                  f"final transport={c.transport()}, hello={got}")
            c.disconnect()
        except Exception as e:
            print(f"[eventlet, TabScope {order} init_app] {transports}: FAILED "
                  f"({type(e).__name__}: {str(e)[:70]})")
    p.terminate(); p.wait(timeout=5)
