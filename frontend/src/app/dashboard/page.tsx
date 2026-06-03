import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const dummyTickets = [
  {
    id: 1,
    sender: "alice@example.com",
    subject: "Login failing after password reset",
    category: "Authentication",
    status: "Open",
  },
  {
    id: 2,
    sender: "bob@company.io",
    subject: "Cannot access invoice PDFs",
    category: "Billing",
    status: "AI-Resolved",
  },
];

export default function TicketBoardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Ticket Board</h1>
        <p className="text-sm text-slate-500 mt-1">
          AI-classified support tickets awaiting review.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">
            Recent Tickets
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Sender</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dummyTickets.map((ticket) => (
                <TableRow key={ticket.id}>
                  <TableCell className="font-medium">
                    {ticket.sender}
                  </TableCell>
                  <TableCell>{ticket.subject}</TableCell>
                  <TableCell>{ticket.category}</TableCell>
                  <TableCell>{ticket.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}