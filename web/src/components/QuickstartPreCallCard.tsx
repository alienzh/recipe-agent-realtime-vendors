"use client";

import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";

import type { VendorOption } from "@/services/api";

type QuickstartPreCallCardProps = {
	isLoading: boolean;
	error: string | null;
	onStartConversation: () => void;
	vendors?: VendorOption[];
	selectedVendor?: string;
	onVendorChange?: (vendor: string) => void;
};

export function QuickstartPreCallCard({
	isLoading,
	error,
	onStartConversation,
	vendors,
	selectedVendor,
	onVendorChange,
}: QuickstartPreCallCardProps) {
	return (
		<div
			className="mx-auto flex w-[min(92vw,26.25rem)] animate-fade-up flex-col items-center rounded-[20px] border border-[#2b2b2b] px-10 py-10 text-center shadow-[0_10px_24px_rgba(0,0,0,0.28)]"
			style={{
				backgroundImage:
					"linear-gradient(164.988deg, rgba(54,54,54,0.2) 1.0596%, rgba(0,0,0,0) 96.089%), linear-gradient(90deg, rgb(16,16,16) 0%, rgb(16,16,16) 100%)",
			}}
		>
			<h1 className="text-[28px] font-medium leading-[1.2] text-white">
				Realtime Vendors
			</h1>
			<p className="mt-[14px] text-sm font-medium leading-6 text-muted-foreground">
				Talk to a single realtime voice-to-voice MLLM, swappable across vendors
				via REALTIME_VENDOR — no separate STT/LLM/TTS. BYO key for the selected
				vendor.
			</p>

			{vendors && vendors.length > 0 ? (
				<div className="mt-6 w-full text-left">
					<label
						htmlFor="realtime-vendor"
						className="text-xs font-medium uppercase tracking-wide text-muted-foreground"
					>
						Realtime vendor
					</label>
					<select
						id="realtime-vendor"
						value={selectedVendor}
						onChange={(e) => onVendorChange?.(e.target.value)}
						disabled={isLoading}
						className="mt-2 h-10 w-full rounded-lg border border-[#2b2b2b] bg-[#101010] px-3 text-sm text-white"
					>
						{vendors.map((v) => (
							<option key={v.name} value={v.name}>
								{v.name}
								{v.needs_key ? "  (needs key)" : "  (key-less)"}
							</option>
						))}
					</select>
					<p className="mt-1 text-[11px] leading-4 text-muted-foreground">
						This recipe is BYO-only — every vendor needs its env vars set on the
						server, otherwise startup reports which are missing.
					</p>
				</div>
			) : null}

			<Button
				onClick={onStartConversation}
				disabled={isLoading}
				className="mt-12 h-10 w-full rounded-lg border border-primary bg-primary text-sm font-medium text-black hover:border-white hover:bg-white hover:text-black disabled:hover:border-primary disabled:hover:bg-primary disabled:hover:text-black"
				aria-label={
					isLoading
						? "Starting conversation with AI agent"
						: "Start conversation with AI agent"
				}
			>
				{isLoading ? (
					<>
						<Loader2 className="h-4 w-4 animate-spin" />
						Starting...
					</>
				) : (
					"Start Conversation"
				)}
			</Button>
			{error ? <p className="mt-3 text-xs text-destructive">{error}</p> : null}
		</div>
	);
}
