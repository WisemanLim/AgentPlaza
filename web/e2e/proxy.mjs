// 컨테이너 안에서 127.0.0.1:<port> → host.docker.internal:<port> 로 넘긴다(콘솔·apps 오리진을 실제 주소 그대로 쓰기 위해).
import net from "node:net";
for (const port of (process.env.PROXY_PORTS ?? "8090,8092").split(",").map(Number)) {
  net.createServer((c) => {
    const u = net.connect(port, "host.docker.internal");
    c.pipe(u).pipe(c);
    const end = () => { c.destroy(); u.destroy(); };
    c.on("error", end); u.on("error", end);
  }).listen(port, "127.0.0.1");
}
