import { auth, currentUser } from "@clerk/nextjs/server";
import { createAnonClient } from "@/lib/supabase/client";
import { redirect } from "next/navigation";
import { ExternalLinkIcon } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import UploadDocumentModal from "@/components/UploadDocumentModal";

// ── Types ──────────────────────────────────

interface TicketRow {
  id: string;
  user_id: string;
  sender_email: string;
  original_subject: string;
  status: string;
  category: string | null;
  external_ticket_url: string | null;
  created_at: string;
  users: { clerk_id: string };
}

// ── Helpers ─────────────────────────────────

async function ensureUserExists() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  const user = await currentUser();
  const email = user?.emailAddresses?.[0]?.emailAddress;

  const supabase = createAnonClient();

  const { data: existing } = await supabase
    .from("users")
    .select("id")
    .eq("clerk_id", userId)
    .maybeSingle();

  if (!existing && email) {
    await supabase.from("users").insert({ clerk_id: userId, email });
  }
}

// ── Page ───────────────────────────────────

export default async function TicketBoardPage() {
  await ensureUserExists();

  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  const supabase = createAnonClient();

  const { data: tickets, error } = await supabase
    .from("tickets")
    .select("*, users!inner(clerk_id)")
    .eq("users.clerk_id", userId)
    .order("created_at", { ascending: false });

  if (error) {
    console.error("Supabase query error:", error.message);
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            Ticket Board
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            AI-classified support tickets awaiting review.
          </p>
        </div>
        <UploadDocumentModal />
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">
            Recent Tickets
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!tickets || tickets.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No tickets yet — they will appear here once inbound emails are
              processed.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Subject</TableHead>
                  <TableHead>Sender</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Trello Link</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(tickets as TicketRow[]).map((ticket) => (
                  <TableRow key={ticket.id}>
                    <TableCell className="font-medium">
                      {ticket.original_subject}
                    </TableCell>
                    <TableCell>{ticket.sender_email}</TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                          ticket.status === "queued"
                            ? "bg-yellow-100 text-yellow-700"
                            : ticket.status === "spam"
                            ? "bg-red-100 text-red-700"
                            : ticket.status === "finalized"
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {ticket.status}
                      </span>
                    </TableCell>
                    <TableCell>
                      {ticket.category ?? (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {ticket.external_ticket_url ? (
                        <a
                          href={ticket.external_ticket_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                        >
                          <ExternalLinkIcon className="size-3" />
                          Open
                        </a>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}