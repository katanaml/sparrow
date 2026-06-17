import { Agent, setGlobalDispatcher } from "undici";

// Override Node.js built-in fetch's undici global dispatcher
// to remove the default 300s headersTimeout which breaks long inference calls.
// Confirmed fix: https://raphael.badia.cc/posts/fixing-headers-timeout-error-with-vercel-ai-sdk
setGlobalDispatcher(new Agent({
  headersTimeout: 30 * 60 * 1000,  // 30 minutes
  bodyTimeout:    30 * 60 * 1000,  // 30 minutes
  connectTimeout: 30 * 1000,       // 30 seconds
}));