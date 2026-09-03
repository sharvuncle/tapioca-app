export default {
  async fetch(request) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", {
        status: 405,
        headers: {
          "Allow": "GET, HEAD"
        }
      });
    }

    const upstream = new URL(request.url);
    upstream.protocol = "https:";
    upstream.hostname = "usetapioca.com";
    upstream.port = "";

    const upstreamRequest = new Request(upstream.toString(), request);

    return fetch(upstreamRequest, {
      redirect: "manual"
    });
  }
};
