# Hodl contracts
An oracle and escrow system for the lightning network. Make LN contracts more expressive.

# Video demo (sorry for the poor audio)

[![](https://i.ibb.co/6NW9KsL/Screenshot-2021-09-21-10-49-12-PM.png)](https://www.youtube.com/watch?v=0Xhdmy6qtGo)

# Screenshots

![](https://i.ibb.co/9scys8S/Screenshot-2021-07-31-12-05-02-AM.png)

![](https://i.ibb.co/7zbC1x4/Screenshot-2021-07-31-12-05-52-AM.png)

If you fire it up, be aware:

1. You need ![lnd](https://github.com/lightningnetwork/lnd/blob/master/docs/INSTALL.md#installation)

2. When you start the app go to localhost:5000/admin/

3. Prepare a draft contract by selecting one of the available templates or make it however you want. The lefthand sidebar now shows all contracts but it needs pagination or something (I'll probably put create a special page instead of putting them in a sidebar). There is also groundwork laid for indicator lights on each existing contract but right now it is always green (indicating "ready to settle") even for contracts that are not ready to settle (which should have a red indicator)

4. On the contract page you have buttons to settle or cancel each party's invoices and buttons to give to the counterparties where they can submit their invoices

5. Send each counterparty their link to where they can submit their invoices

6. Once both counterparties have deposited what they are supposed to, wait for settlement day and settle or cancel the users' invoices as appropriate. The three included contract templates -- trading, lending, and gambling -- all come with instructions which show up on the pages of everyone involved, i.e. the oracle and the counterparties

7. That's basically it, there is no indicator of what happened after you pick a winner (yet), though you can manually check lnd to see if the payment cleared. Eventually there will be an indicator and a number will tick upward to show what you collected in fees. Remember these payments go directly from one counterparty to the other, you do not take custody at any point!

Lots of bug fixes and improvements to come but it's going well!

# Installation instructions

1. Run LND in testnet mode (this app only works on testnet) and unlock your testnet wallet with `lncli unlock`

2. Clone this github repo: `git clone https://github.com/supertestnet/hodlcontracts.git`

3. Enter the hodlcontracts directory: `cd hodlcontracts`

4. Ensure you have python version 3.9 or higher: `python3 --version`

5. Ensure your version of `pip` (the package installer for python) works with python 3.9 or higher: `pip --version` or `pip3 --version`

6. If your version of `pip` is not for python 3.9 or higher but you *do* have `pip3` and it *is* for python 3.9 or higher, replace `pip` with `pip3` in all of the following instructions

8. Create an lnd virtual environment: `virtualenv lnd` or `python3 -m venv lnd`

9. Activate your virtual environment: `source lnd/bin/activate`

10. Install some of the dependencies: `pip install -r requirements.txt`

11. Clone the google api dependency: `git clone https://github.com/googleapis/googleapis.git`

12. Clone the lightning.proto file: `curl -o lightning.proto -s https://raw.githubusercontent.com/lightningnetwork/lnd/master/lnrpc/lightning.proto`

13. Compile the lightning.proto file: `python -m grpc_tools.protoc --proto_path=googleapis:. --python_out=. --grpc_python_out=. lightning.proto`

14. Clone the router.proto file: `curl -o router.proto -s https://raw.githubusercontent.com/lightningnetwork/lnd/master/lnrpc/routerrpc/router.proto`

15. Compile the router.proto file: `python -m grpc_tools.protoc --proto_path=googleapis:. --python_out=. --grpc_python_out=. router.proto`

16. Clone the invoices.proto file: `curl -o invoices.proto -s https://raw.githubusercontent.com/lightningnetwork/lnd/master/lnrpc/invoicesrpc/invoices.proto`

17. Compile the invoices.proto file: `python -m grpc_tools.protoc --proto_path=googleapis:. --python_out=. --grpc_python_out=. invoices.proto`

18. Run hodl contracts: `python3 hodlcontracts.py`

19. Open your browser to the admin page: `http://127.0.0.1:5000/admin/`

20. That's it! It should work from there as displayed in the video. Please raise an issue if it doesn't work for you
