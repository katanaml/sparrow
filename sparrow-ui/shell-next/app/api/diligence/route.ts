import { NextRequest } from "next/server";
import { run_diligence } from "@/app/actions/diligence";
import type { StreamLine } from "@/lib/diligence-types";

// Streams the diligence results to the browser as NDJSON, one DiligenceEvent
// per line, with a heartbeat every 10s so no proxy/tunnel in the path sees an
// idle connection and closes it. All calls to the agent layer run here on the
// server; the browser never sees the Sparrow key or the agent address.
export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      let closed = false;
      const send = (line: StreamLine) => {
        if (closed) return;
        try {
          controller.enqueue(encoder.encode(JSON.stringify(line) + "\n"));
        } catch {
          // controller already closed, ignore
        }
      };

      const heartbeat = setInterval(() => send({ type: "heartbeat" }), 10_000);

      try {
        await run_diligence(formData, send);
      } catch (err) {
        console.error("Diligence stream failed:", err);
        send({ type: "error", message: "Something went wrong while running the checks." });
      } finally {
        closed = true;
        clearInterval(heartbeat);
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "application/x-ndjson",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  });
}