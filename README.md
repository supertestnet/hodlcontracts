# Hodl contracts
A non-custodial oracle and escrow system for the lightning network. Make LN contracts more expressive.

![](https://i.ibb.co/9scys8S/Screenshot-2021-07-31-12-05-02-AM.png)

![](https://i.ibb.co/7zbC1x4/Screenshot-2021-07-31-12-05-52-AM.png)

If you fire it up, be aware:

(1) You need lnd

(2) When you start the app go to localhost:5000/admin/

(3) Prepare a draft contract by selecting one of the available templates or make it however you want. The lefthand sidebar is supposed to show existing contracts but it doesn't do anything right now

(4) On the contract page you have buttons to settle or cancel each party's invoices and buttons to give to the counterparties where they can submit their invoices. Trying to settle an invoice before one user has submitted it and the other has deposited funds to it will crash the server because there is nothing to settle. Eventually this will gracefully fail

(5) Send each counterparty their link to where they can submit their invoices. Eventually I will have an indicator that says whether or not they have done so so that you know what your next step is. It will also show whether the parties have deposited funds to the contract or not

(6) Once both counterparties have deposited what they are supposed to, wait for settlement day and settle or cancel the users' invoices as appropriate. The three included contract templates -- trading, lending, and gambling -- all come with instructions which show up on the pages of everyone involved, i.e. the oracle and the counterparties

(7) That's basically it, there is no indicator of what happened after you pick a winner (yet), though you can manually check lnd to see if the payment cleared. Eventually there will be an indicator and a number will tick upward to show what you collected in fees. Remember these payments go directly from one counterparty to the other, you do not take custody at any point!

(8) I also need to make the server mark the contract complete after you've settled an invoice so that you don't accidentally click the other person later and settle their invoice unfairly

Lots of bug fixes and improvements to come but it's going well!
