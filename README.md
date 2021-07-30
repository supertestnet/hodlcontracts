# Hodl contracts
A non-custodial oracle and escrow system for the lightning network. Make LN contracts more expressive.

[](https://i.ibb.co/FWxpVxW/Screenshot-2021-07-30-12-22-26-AM.png)

[](https://i.ibb.co/YXG22gy/Screenshot-2021-07-30-12-22-29-AM.png)

If you fire it up, be aware:

(1) you need lnd

(2) when you start the app go to localhost:5000/admin/

(3) Prepare a draft contract by selecting one of the available templates or make it however you want. The lefthand sidebar is supposed to show existing contracts but it doesn't do anything right now

(4) There is a blank page where your contract is processed, I haven't yet put that page in the gui yet, it ought to show you the gui with a message about being shortly redirected to the contract page but right now it's just a blank screen with the contract dumped on it

(5) Refresh the contract page (without resubmitting the post data -- i.e. use ctrl-l + enter rather than ctrl-r) and you'll be back in the gui

(6) On the contract page you have buttons to settle a contract one way or the other and buttons to give to the counterparties where they can enter their invoices. Settling the contract before anyone has entered their invoices will just break the page because there is nothing to settle. Eventually this will gracefully fail

(7) Send each counterparty their link to where they can enter their invoices. Eventually I will have an indicator that says whether or not they have done so so that you know what your next step is. For each counterparty, depending on which contract is in use, there are two things they need to do: (1) enter their own invoice (if their contract is one where they have an invoice), (2) pay their counterparty's invoice (if their contract is one where their counterparty has an invoice). Since each counterparty has to do two things (including "waiting on the other counterparty to enter their invoice") there need to be status indicators -- it's on my to do list

(8) Once you are aware that both counterparties have done their part you can now wait for settlement day and pick the winner -- if it's a gambling/predictions contract -- or decide whether or not to settle either one's invoice. The three included contract templates -- trading, lending, and gambling -- all come with instructions which show up on the pages of everyone involved, i.e. the oracle and the counterparties

(9) That's basically it, there is no indicator of what happened after you pick a winner (yet), though I suppose right now you can manually check lnd to see if the payment cleared. Remember these payments are going directly from one counterparty to the other -- you did not take custody at any point! Eventually I will show a nice green checkmark or something to indicate success

(10) I also need to make it close out the contract after you've picked a winner (so you don't accidentally click the other person later and settle their invoice unfairly) and auto cancel any invoice that wasn't picked to be the winner. That isn't "strictly speaking" necessary, as their invoice will eventually expire and their funds will come back to their wallet, but it's nice to do it right away that way there isn't a long delay before the winner gets his or her money back.

Lots of bug fixes and improvements to come but it's going well!
