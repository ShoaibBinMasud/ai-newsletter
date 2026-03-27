"use client";

import { useState, FormEvent } from "react";

type State = "idle" | "loading" | "success" | "error" | "duplicate";

export default function SubscribeForm() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<State>("idle");
  const [errorMsg, setErrorMsg] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setState("loading");

    try {
      const res = await fetch("/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();

      if (res.status === 409) {
        setState("duplicate");
      } else if (!res.ok) {
        setErrorMsg(data.error ?? "Something went wrong. Please try again.");
        setState("error");
      } else {
        setState("success");
        setEmail("");
      }
    } catch {
      setErrorMsg("Network error. Please try again.");
      setState("error");
    }
  }

  if (state === "success") {
    return (
      <div className="bg-white border border-black px-5 py-4 text-center">
        <p className="text-[14px] font-bold text-black">You&rsquo;re subscribed!</p>
        <p className="text-[13px] text-[#555] mt-1">Check your inbox for a welcome email.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
      <input
        type="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="your@email.com"
        className="flex-1 border border-[#ccc] px-4 py-2.5 text-[14px] text-black
                   placeholder:text-[#aaa] focus:outline-none focus:border-black
                   bg-white min-w-0"
      />
      <button
        type="submit"
        disabled={state === "loading"}
        className="bg-black text-white text-[13px] font-bold uppercase tracking-widest
                   px-6 py-2.5 hover:bg-[#f74904] transition-colors duration-150
                   disabled:opacity-50 whitespace-nowrap shrink-0"
      >
        {state === "loading" ? "Subscribing…" : "Subscribe Free"}
      </button>

      {(state === "error" || state === "duplicate") && (
        <p className="w-full text-[12px] text-[#f74904] mt-1">
          {state === "duplicate" ? "This email is already subscribed." : errorMsg}
        </p>
      )}
    </form>
  );
}
