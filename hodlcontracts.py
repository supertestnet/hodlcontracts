import rpc_pb2 as ln
import rpc_pb2_grpc as lnrpc
import invoices_pb2 as invoicesrpc
import invoices_pb2_grpc as invoicesstub
import router_pb2 as routerrpc
import router_pb2_grpc as routerstub
import grpc
import os
import codecs
import requests
import json
import time
#kangle is dope 
import nympy
import sqlite3
import math
from random import *
from hashlib import sha256
from stem.control import Controller
from flask import Flask, redirect, url_for, request, make_response

os.environ[ "GRPC_SSL_CIPHER_SUITES" ] = 'HIGH+ECDSA'
cert = open( os.path.expanduser( '~/.lnd/tls.cert' ), 'rb' ).read()

with open( os.path.expanduser( '~/.lnd/data/chain/bitcoin/testnet/admin.macaroon'), 'rb' ) as f:
    macaroon_bytes = f.read()
    macaroon = codecs.encode( macaroon_bytes, 'hex' )

def metadata_callback( context, callback ):
    callback( [ ( 'macaroon', macaroon ) ], None)

cert_creds = grpc.ssl_channel_credentials( cert )
auth_creds = grpc.metadata_call_credentials( metadata_callback )
combined_creds = grpc.composite_channel_credentials( cert_creds, auth_creds )
channel = grpc.secure_channel( 'localhost:10009', combined_creds )
stub = lnrpc.LightningStub( channel )
stub.GetInfo( ln.GetInfoRequest() )

def getInvoice( expiry, hash, amount ):
    stub2 = invoicesstub.InvoicesStub( channel )
    request = invoicesrpc.AddHoldInvoiceRequest(
        hash=hash.decode( "hex" ),
        value=amount,
        expiry=expiry,
    )
    return stub2.AddHoldInvoice( request ).payment_request

def settleInvoice( preimage ):
    addLog( "settle invoice is running with this preimage: " + preimage )
    stub2 = invoicesstub.InvoicesStub( channel )
    request = invoicesrpc.SettleInvoiceMsg(
        preimage=preimage.decode( "hex" )
    )
    return stub2.SettleInvoice( request )

def cancelInvoice( pmthash ):
    stub2 = invoicesstub.InvoicesStub( channel )
    request = invoicesrpc.CancelInvoiceMsg(
        payment_hash=pmthash.decode( "hex" )
    )
    return stub2.CancelInvoice( request )

def getStatus( id, party ):
    contract_id = id
    con = sqlite3.connect( "contracts.db" )
    cur = con.cursor()
    cur.execute( "SELECT contract from contracts WHERE contract_id = '" + contract_id + "'" )
    contracts = cur.fetchone()
    con.close()
    datum = json.loads( contracts[ 0 ] )
    if int( party ) == 1 and str( datum[ "first party original invoice" ] ) == "":
        status = "No interaction yet"
    if int( party ) == 1 and str( datum[ "first party original invoice" ] ) != "":
        pmthash = str( datum[ "first party pmthash" ] )
        request = ln.PaymentHash(
            r_hash_str=pmthash
        )
        response = stub.LookupInvoice( request )
        pmtstatus = response.state
        if pmtstatus == 3:
            status = "Contract funded, awaiting settlement"
        elif pmtstatus == 2:
            status = "Canceled"
        elif pmtstatus == 1:
            status = "Settled"
        else:
            status = "Waiting on other party"
    if int( party ) == 2 and str( datum[ "second party original invoice" ] ) == "":
        if str( datum[ "first party original invoice" ] ) == "":
            status = "Waiting for other party"
        else:
            status = "No interaction yet"
    if int( party ) == 2 and str( datum[ "second party original invoice" ] ) != "":
        if str( datum[ "first party original invoice" ] ) == "":
            status = "Waiting for other party"
        else:
            status = "No interaction yet"
        pmthash = str( datum[ "second party pmthash" ] )
        request = ln.PaymentHash(
            r_hash_str=pmthash
        )
        response = stub.LookupInvoice( request )
        pmtstatus = response.state
        if pmtstatus == 3:
            status = "Contract funded, awaiting settlement"
        elif pmtstatus == 2:
            status = "Canceled"
        elif pmtstatus == 1:
            status = "Settled"
        else:
            status = "Waiting on other party"
    returnable = status
    return returnable

"""
def payFirstParty( pmthash ):
    returnable = "payment failed"
    con = sqlite3.connect( "contracts.db" )
    cur = con.cursor()
    cur.execute( "SELECT first_party_original from contracts WHERE first_party_pmthash = '" + pmthash + "'" )
    contract = cur.fetchone()
    con.close()
    original_invoice = ''.join( contract )
    stub3 = routerstub.RouterStub( channel )
    trypay = routerrpc.SendPaymentRequest(
        payment_request=original_invoice,
        timeout_seconds=15,
        fee_limit_sat=10
    )
    fullresponse = []
    for response in stub3.SendPayment( trypay ):
        fullresponse.append( response )
    if len( fullresponse ) > 2:
        pmtstatus = fullresponse[ 2 ].state
        if pmtstatus == 1:
            pmtpmgbytes = str( fullresponse[ 2 ].preimage )
            pmtpmghex = "".join("{:02x}".format(ord(c)) for c in pmtpmgbytes)
            returnable = repr( settleInvoice( pmtpmghex ) )

def paySecondParty( pmthash ):
    returnable = "payment failed"
    con = sqlite3.connect( "contracts.db" )
    cur = con.cursor()
    cur.execute( "SELECT second_party_original from contracts WHERE first_party_pmthash = '" + pmthash + "'" )
    contract = cur.fetchone()
    con.close()
    original_invoice = ''.join( contract )
    stub3 = routerstub.RouterStub( channel )
    trypay = routerrpc.SendPaymentRequest(
        payment_request=original_invoice,
        timeout_seconds=15,
        fee_limit_sat=10
    )
    fullresponse = []
    for response in stub3.SendPayment( trypay ):
        fullresponse.append( response )
    if len( fullresponse ) > 2:
        pmtstatus = fullresponse[ 2 ].state
        if pmtstatus == 1:
            pmtpmgbytes = str( fullresponse[ 2 ].preimage )
            pmtpmghex = "".join("{:02x}".format(ord(c)) for c in pmtpmgbytes)
            returnable = repr( settleInvoice( pmtpmghex ) )
"""
def makeHash():
    rand1 = int( math.floor( random() * 100000000000 ) )
    rand2 = int( math.floor( random() * 100000000000 ) )
    rand3 = int( math.floor( random() * 100000000000 ) )
    rand4 = int( math.floor( random() * 100000000000 ) )
    rand5 = int( math.floor( random() * 100000000000 ) )
    rand6 = int( math.floor( random() * 100000000000 ) )
    rand7 = int( math.floor( random() * 100000000000 ) )
    rand = str( rand1 ) + str( rand2 ) + str( rand3 ) + str( rand4 ) + str( rand5 ) + str( rand6 ) + str( rand7 )
    return sha256( rand.encode( 'utf-8' ) ).hexdigest()

def addLog( texttoadd ):
    with open( 'debug.log', 'a' ) as f:
        f.write( texttoadd + "\n" )

app = Flask(__name__)

@app.route( '/checkstatus/', methods=[ 'POST', 'GET' ] )
def checkStatus():
    from flask import request
    id = request.args.get( "id" )
    party = request.args.get( "party" )
    response = make_response(getStatus( id, party ), 200)
    response.mimetype = "text/plain"
    return response

@app.route( '/cancel/', methods=[ 'POST', 'GET' ] )
def canceler():
    from flask import request
    contract_id = request.args.get( "id" )
    party = request.args.get( "party" )
    con = sqlite3.connect( "contracts.db" )
    cur = con.cursor()
    cur.execute( "SELECT contract from contracts WHERE contract_id = '" + contract_id + "'" )
    contracts = cur.fetchone()
    con.close()
    datum = json.loads( contracts[ 0 ] )
    if int( party ) == 1:
        pmthash = str( datum[ "first party pmthash" ] )
    else:
        pmthash = str( datum[ "second party pmthash" ] )
    returnable = repr( cancelInvoice( pmthash ) )
    return returnable

@app.route( '/settle/', methods=[ 'POST', 'GET' ] )
def settler():
    from flask import request
    contract_id = request.args.get( "id" )
    trueorfalse = request.args.get( "true" )
    con = sqlite3.connect( "contracts.db" )
    cur = con.cursor()
    cur.execute( "SELECT contract from contracts WHERE contract_id = '" + contract_id + "'" )
    contracts = cur.fetchone()
    con.close()
    datum = json.loads( contracts[ 0 ] )
    if int( trueorfalse ) == 1:
        pmthash = str( datum[ "first party pmthash" ] )
        request = ln.PaymentHash(
            r_hash_str=pmthash
        )
        response = stub.LookupInvoice( request )
        status = response.state
        if status == 3:
            addLog( "status: " + str( status ) )
            original_invoice = str( datum[ "first party original invoice" ] )
            addLog( "original invoice: " + str( datum[ "first party original invoice" ] ) )
            stub3 = routerstub.RouterStub( channel )
            trypay = routerrpc.SendPaymentRequest(
                payment_request=original_invoice,
                timeout_seconds=900,
                fee_limit_sat=10
            )
            fullresponse = []
            for response in stub3.SendPayment( trypay ):
                fullresponse.append( response )
            addLog( "full response: \n" + repr( fullresponse ) )
            if len( fullresponse ) > 2:
                pmtstatus = fullresponse[ 2 ].state
                addLog( "payment status: " + str( pmtstatus ) )
                if pmtstatus == 1:
                    pmtpmgbytes = str( fullresponse[ 2 ].preimage )
                    pmtpmghex = "".join("{:02x}".format(ord(c)) for c in pmtpmgbytes)
                    addLog( "payment preimage hex: " + pmtpmghex )
                    settleInvoice( pmtpmghex )
                    return pmtpmghex
    else:
        pmthash = str( datum[ "second party pmthash" ] )
        request = ln.PaymentHash(
            r_hash_str=pmthash
        )
        response = stub.LookupInvoice( request )
        status = response.state
        if status == 3:
            original_invoice = str( datum[ "second party original invoice" ] )
            stub3 = routerstub.RouterStub( channel )
            trypay = routerrpc.SendPaymentRequest(
                payment_request=original_invoice,
                timeout_seconds=900,
                fee_limit_sat=10
            )
            fullresponse = []
            for response in stub3.SendPayment( trypay ):
                fullresponse.append( response )
            if len( fullresponse ) > 2:
                pmtstatus = fullresponse[ 2 ].state
                if pmtstatus == 1:
                    pmtpmgbytes = str( fullresponse[ 2 ].preimage )
                    pmtpmghex = "".join("{:02x}".format(ord(c)) for c in pmtpmgbytes)
                    settleInvoice( pmtpmghex )
                    return pmtpmghex
    return ""

@app.route( '/contract/', methods=[ 'POST', 'GET' ] )
def contractpage():
    returnable = ""
    if request.form.get( "contract name" ) is not None and request.args.get( "processing" ) is not None:
        if request.args.get( "id" ) is not None:
            contract_id = request.args.get( "id" )
            contract_name = request.form.get( "contract name" )
            description = request.form.get( "description" )
            first_party_role = request.form.get( "first partys role" )
            first_party_amount = request.form.get( "first partys amount" )
            second_party_role = request.form.get( "second partys role" )
            second_party_amount = request.form.get( "second partys amount" )
            settlement_date = request.form.get( "settlement date" )
            automatic = 0
            btc_price = ""
            usdt_amount = ""
            usdt_address = ""
            if request.form.get( "btc price checkbox" ) is not None or request.form.get( "usdt checkbox" ) is not None:
                automatic = 1
                if request.form.get( "btc price" ) is not None:
                    btc_price = request.form.get( "btcvprice" )
                if request.form.get( "usdt amount" ) is not None:
                    usdt_amount = request.form.get( "usdt amount" )
                if request.form.get( "usdt address" ) is not None:
                    usdt_address = request.form.get( "usdt address" )
            oracle_fee = request.form.get( "oracle fee" )
            contract_params = {
                "contract id": contract_id,
                "contract name": contract_name,
                "description": description,
                "first party role": first_party_role,
                "first party amount": first_party_amount,
                "first party original invoice": "",
                "first party hodl invoice": "",
                "first party pmthash": "",
                "private": 1,
                "second party role": second_party_role,
                "second party amount": second_party_amount,
                "second party original invoice": "",
                "second party hodl invoice": "",
                "second party pmthash": "",
                "settlement date": settlement_date,
                "automatic": automatic,
                "btc_price": btc_price,
                "usdt_amount": usdt_amount,
                "usdt_address": usdt_address,
                "oracle_fee": oracle_fee
            }
            contract = json.dumps( contract_params )
            con = sqlite3.connect( "contracts.db" )
            cur = con.cursor()
            cur.execute( """CREATE TABLE IF NOT EXISTS contracts (
                        contract text,
                        contract_id text,
                        contract_name text,
                        description text,
                        first_party_role text,
                        first_party_amount integer,
                        first_party_original text,
                        first_party_hodl text,
                        first_party_pmthash text,
                        second_party_role text,
                        second_party_amount text,
                        second_party_original text,
                        second_party_hodl text,
                        second_party_pmthash text,
                        settlement_date integer,
                        automatic integer,
                        btc_price integer,
                        usdt_amount integer,
                        usdt_address text,
                        private integer,
                        oracle_fee integer
                        )""" )
            con.commit()
            cur.execute( "INSERT INTO contracts VALUES ( :contract, :contract_id, :contract_name, :description, :first_party_role, :first_party_amount, :first_party_original, :first_party_hodl, :first_party_pmthash, :second_party_role, :second_party_amount, :second_party_original, :second_party_hodl, :second_party_pmthash, :settlement_date, :automatic, :btc_price, :usdt_amount, :usdt_address, :private, :oracle_fee )",
                       { "contract": contract, "contract_id": contract_id, "contract_name": contract_name, "description": description, "first_party_role": first_party_role, "first_party_amount": first_party_amount, "first_party_original": "", "first_party_hodl": "", "first_party_pmthash": "", "second_party_role": second_party_role, "second_party_amount": second_party_amount, "second_party_original": "", "second_party_hodl": "", "second_party_pmthash": "", "settlement_date": settlement_date, "automatic": automatic, "btc_price": btc_price, "usdt_amount": usdt_amount, "usdt_address": usdt_address, "private": 0, "oracle_fee": oracle_fee } )
            con.commit()
            cur.execute( "SELECT * from contracts WHERE contract_id = '" + contract_id + "'" )
            contracts = cur.fetchone()
            con.close()
            fullcontract = json.dumps( contracts )
            returnable = """
                <body style="margin: 0px; font-family: Helvetica, sans-serif;">
                        <div id="header" style="height: 50px; background-color: red;">
                                <h1 style="padding: 7px; color: white;">
                                        Hodl contracts
                                </h1>
                        </div>
                        <div id="leftside" style="position: absolute; left: 0px; top: 50px; background-color: orange; width: 25%; height: 100%;">
                        </div>
                        <div id="middle" style="width: 50%; margin: auto;">
                                <div style="margin: 10px;">
                                        <h2>
                                                Contract {contract_id_short}
                                        </h2>
                                        <p>
						Your submission is being processed. If you are not redirected shortly, <a href="/contract/?id={contract_id}">click here</a>
					</p>
                                </div>
                        </div>
                        <div id="rightside" style="position: absolute; right: 0px; top: 50px; background-color: blue; width: 25%; height: 100%;">
                                <div style="margin: 10px; color: white;">
                                </div>
                        </div>
                        <script>
                                function longBars() {{
                                        document.getElementById( "leftside" ).style.height = document.getElementById( "all contracts" ).offsetHeight + "px";
                                        document.getElementById( "rightside" ).style.height = document.getElementById( "all contracts" ).offsetHeight + "px";
                                }}
                                longBars();
                        </script>
                        <script>
				setTimeout( function() {{ window.location.href = "/contract/?id={contract_id}" }}, 2500 );
                        </script>
                </div>
            """.format( contract_id_short = contract_id[ 0:10 ] + "...", contract_id = contract_id, fullcontract = fullcontract )
    else:
        if request.args.get( "id" ) is not None:
            contract_id = request.args.get( "id" )
            con = sqlite3.connect( "contracts.db" )
            cur = con.cursor()
            cur.execute( "SELECT contract FROM contracts WHERE contract_id = '" + contract_id + "'" )
            contracts = cur.fetchone()
            cur.execute( "SELECT contract FROM contracts" )
            allcontracts = cur.fetchall()
            set = '['
            for ct in allcontracts:
                set += json.dumps( json.loads( ct[ 0 ] ) ) + ","
            set = set[0:-1]
            set += ']'
            allcontractsstring = set
            con.close()
            datum = json.loads( contracts[ 0 ] )
            first_party_amount = str( datum[ "first party amount" ] )
            second_party_amount = str( datum[ "second party amount" ] )
            contract = json.dumps( datum )
            returnable = """
                <body style="margin: 0px; font-family: Helvetica, sans-serif;">
                        <div id="header" style="height: 50px; background-color: red;">
                                <h1 style="padding: 7px; color: white;">
                                        Hodl contracts
                                </h1>
                        </div>
                        <div id="leftside" style="position: absolute; left: 0px; top: 50px; background-color: orange; width: 25%; height: 100%;">
                                <div style="margin: 10px;">
                                        <h2>
                                                All contracts
                                        </h2>
					<p id="all contracts">
					</p>
                                </div>
                        </div>
                        <div id="middle" style="width: 50%; margin: auto;">
                                <div style="margin: 10px;">
                                        <h2>
                                                Contract {contract_id_short}
                                        </h2>
                                        <div align="center">
						<div id="1st party" style="display: inline-block; margin-left: 20px; margin-right: 20px;">
							<p style="font-weight: bold; margin-bottom: 20px;">First party</p>
							<p><span style="text-decoration: underline;">Status</span>: <span id="1status"></span></p>
	                                                <a id="1st party settlement" target="_blank">
								<button type="button" id="first party settle button" style="color: white; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px; cursor: not-allowed; margin-bottom: 20px; background-color: green; opacity: 0.3">
									Settle
								</button>
							</a>
							<br>
	                                                <a id="1st party cancelation" target="_blank">
								<button type="button" id="first party cancel button" style="color: white; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px; cursor: not-allowed; margin-bottom: 20px; background-color: red; opacity: 0.3">
									Cancel
								</button>
							</a>
						</div>
						<div id="2nd party" style="display: inline-block; margin-left: 20px; margin-right: 20px;">
							<p style="font-weight: bold; margin-bottom: 20px;">Second party</p>
							<p><span style="text-decoration: underline;">Status</span>: <span id="2status"></span></p>
	                                                <a id="2nd party settlement" target="_blank">
								<button type="button" id="second party settle button" style="color: white; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px; cursor: not-allowed; margin-bottom: 20px; background-color: green; opacity: 0.3">
									Settle
								</button>
							</a>
							<br>
	                                                <a id="2nd party cancelation" target="_blank">
								<button type="button" id="second party cancel button" style="color: white; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px; cursor: not-allowed; margin-bottom: 20px; background-color: red; opacity: 0.3">
									Cancel
								</button>
							</a>
						</div>
                                        </div>
                                        <p id="description">
					</p>
					<p>
						Please send each counterparty a link to their page
					</p>
                                        <p align="center">
                                                <a id="1st party link" target="_blank"><button type="button" style="border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px; cursor: pointer;">1st party's page</button></a>
                                                <a id="2nd party link" target="_blank"><button type="button" style="border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px; cursor: pointer;">2nd party's page</button></a>
                                        </p>
                                </div>
                        </div>
                        <div id="rightside" style="position: absolute; right: 0px; top: 50px; background-color: blue; width: 25%; height: 100%;">
                                <div style="margin: 10px; color: white;">
                                        <h2>
                                                New contract
                                        </h2>
                                        <div id="new contract" class="sidebarbtn" style="border: 2px solid white; border-radius: 5px; height: 40px; font-size: 18px; line-height: 40px; margin-bottom: 20px; cursor: pointer; text-align: center;">
                                                Create new contract
                                        </div>
                                </div>
                        </div>
                        <script>
                                function longBars() {{
                                        document.getElementById( "leftside" ).style.height = document.getElementById( "all contracts" ).offsetHeight + "px";
                                        document.getElementById( "rightside" ).style.height = document.getElementById( "all contracts" ).offsetHeight + "px";
                                }}
                                longBars();
                        </script>
                        <script>
                                document.getElementById( "new contract" ).addEventListener( "click", function() {{
                                        window.location.href = "/admin/";
                                }});
                        </script>
			<script>
                                function makeCBox( name, date, id ) {{
                                        div = '<a href="/contract/?id=' + id + '" style="text-decoration: none;"><div class="cbox" style="padding: 10px; background-color: white; border-radius: 10px; box-shadow: black 2px 2px 5px; margin-bottom: 10px; color: black;"><div class="clight" align="right" style="color: #4fd83a;">&#9673;</div><div class="cname">' + name + '</div><div class="sdate" style="font-size: 14px; font-style: italic; margin-top: 5px;" align="right">' + date + '</div></div></a>';
                                        return div;
                                }}
				var allcontracts = {allcontracts};
				allcontracts.reverse();
                                allcontracts.forEach( function( item ) {{
					document.getElementById( "all contracts" ).innerHTML += makeCBox( item[ "contract name" ], item[ "settlement date" ], item[ "contract id" ] );
				}});
                                longBars();
			</script>
                        <script>
				function checkStatus( party ) {{
					var xhttp = new XMLHttpRequest();
					xhttp.onreadystatechange = function() {{
						if ( this.readyState == 4 && this.status == 200 ) {{
							document.getElementById( party + "status" ).innerText = xhttp.responseText;
							if ( party == 1 ) {{
								if ( xhttp.responseText == "Waiting on other party" ) {{
		                                			document.getElementById( "1st party settlement" ).removeAttribute( "href" );
									document.getElementById( "first party settle button" ).style.cursor = "not-allowed";
									document.getElementById( "first party settle button" ).style.opacity = "0.3";
		                                			document.getElementById( "1st party cancelation" ).href = "/cancel/?id=" + json[ "contract id" ] + "&party=1";
									document.getElementById( "first party cancel button" ).style.cursor = "pointer";
									document.getElementById( "first party cancel button" ).style.opacity = 1;
								}} else if ( xhttp.responseText == "Contract funded, awaiting settlement" ) {{
		                                			document.getElementById( "1st party settlement" ).href = "/settle/?id=" + json[ "contract id" ] + "&true=1";
									document.getElementById( "first party settle button" ).style.cursor = "pointer";
									document.getElementById( "first party settle button" ).style.opacity = 1;
		                                			document.getElementById( "1st party cancelation" ).href = "/cancel/?id=" + json[ "contract id" ] + "&party=1";
									document.getElementById( "first party cancel button" ).style.cursor = "pointer";
									document.getElementById( "first party cancel button" ).style.opacity = 1;
								}} else {{
		                                			document.getElementById( "1st party settlement" ).removeAttribute( "href" );
									document.getElementById( "first party settle button" ).style.cursor = "not-allowed";
									document.getElementById( "first party settle button" ).style.opacity = "0.3";
		                                			document.getElementById( "1st party cancelation" ).removeAttribute( "href" );
									document.getElementById( "first party cancel button" ).style.cursor = "not-allowed";
									document.getElementById( "first party cancel button" ).style.opacity = "0.3";
								}}
							}}
							if ( party == 2 ) {{
								if ( xhttp.responseText == "Waiting on other party" ) {{
                		        			        document.getElementById( "2nd party settlement" ).removeAttribute( "href" );
									document.getElementById( "second party settle button" ).style.cursor = "not-allowed";
									document.getElementById( "second party settle button" ).style.opacity = "0.3";
					                                document.getElementById( "2nd party cancelation" ).href = "/cancel/?id=" + json[ "contract id" ] + "&party=2";
									document.getElementById( "second party cancel button" ).style.cursor = "pointer";
									document.getElementById( "second party cancel button" ).style.opacity = 1;
								}} else if ( xhttp.responseText == "Contract funded, awaiting settlement" ) {{
                		        			        document.getElementById( "2nd party settlement" ).href = "/settle/?id=" + json[ "contract id" ] + "&true=0";
									document.getElementById( "second party settle button" ).style.cursor = "pointer";
									document.getElementById( "second party settle button" ).style.opacity = 1;
					                                document.getElementById( "2nd party cancelation" ).href = "/cancel/?id=" + json[ "contract id" ] + "&party=2";
									document.getElementById( "second party cancel button" ).style.cursor = "pointer";
									document.getElementById( "second party cancel button" ).style.opacity = 1;
								}} else {{
                		        			        document.getElementById( "2nd party settlement" ).removeAttribute( "href" );
									document.getElementById( "second party settle button" ).style.cursor = "not-allowed";
									document.getElementById( "second party settle button" ).style.opacity = "0.3";
					                                document.getElementById( "2nd party cancelation" ).removeAttribute( "href" );
									document.getElementById( "second party cancel button" ).style.cursor = "not-allowed";
									document.getElementById( "second party cancel button" ).style.opacity = "0.3";
								}}
							}}
							console.log( "first party amount: {fpamt}" );
							console.log( "second party amount: {spamt}" );
						}}
					}}
					xhttp.open( "GET", "/checkstatus/?id={contract_id}&party=" + party, true );
					xhttp.send();
				}}
				function loopStatus( party ) {{
					checkStatus( party );
					if ( document.getElementById( party + "status" ).innerText != "Canceled" && document.getElementById( party + "status" ).innerText != "Settled" ) {{
						setTimeout( function() {{ loopStatus( party ); }}, 5000 );
					}}
				}}
				loopStatus( 1 );
				loopStatus( 2 );
                        </script>
                        <script>
                                json = {contract};
                                document.getElementById( "description" ).innerText = json[ "description" ];
                                document.getElementById( "1st party link" ).href = "/?id=" + json[ "contract id" ] + "&party=1";
                                document.getElementById( "2nd party link" ).href = "/?id=" + json[ "contract id" ] + "&party=2";
                        </script>
                </div>
            """.format( contract_id_short = contract_id[ 0:10 ] + "...", contract_id = contract_id, contract = contract, allcontracts = allcontractsstring, fpamt = first_party_amount, spamt = second_party_amount )
    return returnable

@app.route( '/admin/', methods=[ 'POST', 'GET' ] )
def adminpage():
    contract_id = makeHash()
    con = sqlite3.connect( "contracts.db" )
    cur = con.cursor()
    cur.execute( "SELECT contract FROM contracts" )
    allcontracts = cur.fetchall()
    set = '['
    for ct in allcontracts:
        set += json.dumps( json.loads( ct[ 0 ] ) ) + ","
    set = set[0:-1]
    set += ']'
    allcontractsstring = set
    con.close()
    returnable = """
                <body style="margin: 0px; font-family: Helvetica, sans-serif;">
                        <div id="header" style="height: 50px; background-color: red;">
                                <h1 style="padding: 7px; color: white;">
                                        Hodl Contracts
                                </h1>
                        </div>
                        <div id="leftside" style="position: absolute; left: 0px; top: 50px; background-color: orange; width: 25%; height: 100%;">
                                <div style="margin: 10px;">
                                        <h2>
                                                All contracts
                                        </h2>
					<p id="all contracts">
					</p>
                                </div>
                        </div>
                        <div id="middle" style="width: 50%; margin: auto;">
                                <div style="margin: 10px;">
                                        <h2>
                                                New contract
                                        </h2>
                                        <form method="post" action="/contract/?id={contract_id}&processing=true">
                                                <p style="font-weight: bold;">
                                                        Contract name
                                                </p>
                                                <input type="text" style="width: 100%; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" id="contract name" name="contract name">
                                                <p style="font-weight: bold;">
                                                        Contract description
                                                </p>
                                                <textarea style="width: 100%; border: 2px solid black; border-radius: 5px; height: 140px; font-family: Helvetica, sans-serif; font-size: 18px;" type="text" id="description" name="description"></textarea>
                                                <p style="font-weight: bold;">
                                                        Settlement date
                                                </p>
                                                <input type="date" placeholder="12/25/2020" style="width: 100%; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" type="text" id="settlement date" name="settlement date">
                                                <p style="font-weight: bold;">
                                                        First party's role
                                                </p>
                                                <input type="text" style="width: 100%; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" id="first partys role" name="first partys role" placeholder="Buyer">
                                                <p style="font-weight: bold;">
                                                        Second party's role
                                                </p>
                                                <input type="text" style="width: 100%; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" id="second partys role" name="second partys role" placeholder="Seller">
                                                <p style="font-weight: bold;">
                                                        How much will the first party send to the second party via bitcoin?
                                                </p>
                                                <span>$</span> <input type="number" style="width: 90%; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" id="first partys amount" name="first partys amount" placeholder="100.00">
                                                <p style="font-weight: bold;">
                                                        How much will the second party send to the first party via bitcoin?
                                                </p>
                                                <span>$</span> <input type="number" style="width: 90%; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" id="second partys amount" name="second partys amount" placeholder="0.00">
                                                <p style="font-weight: bold;">
                                                        Oracle fee
                                                </p>
                                                <span>$</span> <input type="number" style="width: 90%; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" id="oracle fee" name="oracle fee" placeholder="1.00" step="0.01">
                                                <h3 style="text-decoration: underline; cursor: pointer;" onclick="if ( this.nextElementSibling.style.display != 'none' ) {{this.nextElementSibling.style.display = 'none'; }} else {{this.nextElementSibling.style.display = 'block';}} longBars();">
                                                        Advanced (only for automated oracle contracts)
                                                </h3>
                                                <div id="advanced options" style="display: none;">
                                                        <div style="margin-bottom: 20px;">
								<p>
									Be aware that if you check either of these boxes your contract will execute automatically on the settlement date you specify above
								</p>
                                                                <input type="checkbox" id="btc price checkbox" name="btc price checkbox">
                                                                <label for="btc price checkbox">
                                                                        Price condition: if bitcoin's price is above <span>$</span> <input type="number" style="width: 120px; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" id="btc price" name="btc price" placeholder="100000.00"> send the btc to the first party, otherwise it will be sent to the second party
                                                                </label>
                                                        </div>
                                                        <div>
                                                                <input type="checkbox" id="usdt checkbox" name="usdt checkbox">
                                                                <label for="usdt checkbox">
                                                                        USDT condition: if omni explorer says that an output of <span>$</span> <input type="number" style="width: 120px; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" id="usdt amount" name="usdt amount" placeholder="100.00"> or more USDT was in <input type="text" style="width: 120px; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" id="usdt address" name="usdt address" placeholder="1abc234def567ghi"> address, it will be sent to the first party, otherwise it will be sent to the second party
                                                                </label>
                                                        </div>
                                                </div>
                                                <p>
                                                        <button type="submit" style="border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px; cursor: pointer;">Submit</button>
                                                </p>
                                        </form>
                                </div>
                        </div>
                        <div id="rightside" style="position: absolute; right: 0px; top: 50px; background-color: blue; width: 25%; height: 100%;">
                                <div style="margin: 10px; color: white;">
                                        <h2>
                                                Contract templates
                                        </h2>
                                        <div id="trading template" class="sidebarbtn" style="border: 2px solid white; border-radius: 5px; height: 40px; font-size: 18px; line-height: 40px; margin-bottom: 20px; cursor: pointer; text-align: center;">
                                                Trading contract
                                        </div>
                                        <div id="loan template" class="sidebarbtn" style="border: 2px solid white; border-radius: 5px; height: 40px; font-size: 18px; line-height: 40px; margin-bottom: 20px; cursor: pointer; text-align: center;">
                                                Loan contract
                                        </div>
                                        <div id="betting template" class="sidebarbtn" style="border: 2px solid white; border-radius: 5px; height: 40px; font-size: 18px; line-height: 40px; margin-bottom: 20px; cursor: pointer; text-align: center;">
                                                Betting contract
                                        </div>
                                </div>
                        </div>
                        <script>
                                function longBars() {{
                                        document.getElementById( "leftside" ).style.height = document.body.offsetHeight + "px";
                                        document.getElementById( "rightside" ).style.height = document.body.offsetHeight + "px";
                                }}
                                longBars();
                        </script>
			<script>
                                function makeCBox( name, date, id ) {{
                                        div = '<a href="/contract/?id=' + id + '" style="text-decoration: none;"><div class="cbox" style="padding: 10px; background-color: white; border-radius: 10px; box-shadow: black 2px 2px 5px; margin-bottom: 10px; color: black;"><div class="clight" align="right" style="color: #4fd83a;">&#9673;</div><div class="cname">' + name + '</div><div class="sdate" style="font-size: 14px; font-style: italic; margin-top: 5px;" align="right">' + date + '</div></div></a>';
                                        return div;
                                }}
				var allcontracts = {allcontracts};
				allcontracts.reverse();
                                allcontracts.forEach( function( item ) {{
					document.getElementById( "all contracts" ).innerHTML += makeCBox( item[ "contract name" ], item[ "settlement date" ], item[ "contract id" ] );
				}});
                                longBars();
			</script>
                        <script>
				function checkStatus( party ) {{
					var xhttp = new XMLHttpRequest();
					xhttp.onreadystatechange = function() {{
						if ( this.readyState == 4 && this.status == 200 ) {{
							document.getElementById( party + "status" ).innerText = xhttp.responseText;
						}}
					}}
					xhttp.open( "GET", "/checkstatus/?id={contract_id}&party=" + party, true );
					xhttp.send();
				}}
				function loopStatus( party ) {{
					checkStatus( party );
					if ( document.getElementById( party + "status" ).innerText != "Canceled" && document.getElementById( party + "status" ).innerText != "Settled" ) {{
						setTimeout( function() {{ loopStatus( party ); }}, 5000 );
					}}
				}}
                        </script>
                        <script>
                                document.getElementById( "trading template" ).addEventListener( "click", function() {{
                                        document.getElementById( "contract name" ).value = "Janice trades with Joe, $100 in bitcoin for $100 in usd";
                                        document.getElementById( "description" ).value = "The 1st party submits an invoice for $100 and hands the 2nd party $100 usd. The 2nd party pays the invoice and the oracle settles that invoice. This completes the contract in the happy case. There are two unhappy cases. If the 2nd party doesn't send the bitcoins, the contract expires on the settlement date. No one loses any money but no one is happy. If the 1st party doesn't hand over the usd, the oracle cancels the 1st party's invoice. No one loses any money but no one is happy.";
					var d = new Date();
                                        document.getElementById( "settlement date" ).value = d.toISOString().substr( 0, 10 );
                                        document.getElementById( "first partys role" ).value = "Bitcoin buyer";
                                        document.getElementById( "second partys role" ).value = "Bitcoin seller";
                                        document.getElementById( "first partys amount" ).value = "0.00";
                                        document.getElementById( "second partys amount" ).value = "100.00";
                                        document.getElementById( "oracle fee" ).value = "1.00";
                                }});
                                document.getElementById( "loan template" ).addEventListener( "click", function() {{
                                        document.getElementById( "contract name" ).value = "Timothy lends $100 to Olivia";
                                        document.getElementById( "description" ).value = "The 1st party submits an invoice for $200 and hands over $100 usd. The 2nd party pays the invoice to overcollateralize his position. By the settlement date he hands back the $100 usd plus interest. The oracle cancels the 1st party's invoice. This concludes the contract in the happy case. There are several unhappy cases. If the 1st party does not submit an invoice, no one loses any money but no one is happy. If the 1st party submits an invoice and the 2nd party pays it but the 1st party doesn't hand over the usd by the settlement date, the oracle cancels the invoice. No one loses any money but no one is happy. If the 1st party does everything right but the 2nd party doesn't hand over the usd plus interest, the oracle settles the invoice and the lender uses it to cover his losses. The borrower loses money and is unhappy but he also is to blame because he did not pay his principle plus interest. If the price of bitcoin dips and the collateral is nearly not worth $100 anymore, the oracle settles the invoice. The lender keeps a bit more than $100 in btc and the borrower keeps $100 in usd. Neither one is perfectly happy but it's fair enough that many will be fine with it.";
					var d = new Date();
                                        document.getElementById( "settlement date" ).value = d.toISOString().substr( 0, 10 );
                                        document.getElementById( "first partys role" ).value = "Lender";
                                        document.getElementById( "second partys role" ).value = "Borrower";
                                        document.getElementById( "first partys amount" ).value = "0.00";
                                        document.getElementById( "second partys amount" ).value = "200.00";
                                        document.getElementById( "oracle fee" ).value = "1.00";
                                }});
                                document.getElementById( "betting template" ).addEventListener( "click", function() {{
                                        document.getElementById( "contract name" ).value = "The Steeltops versus the Rockets";
                                        document.getElementById( "description" ).value = "Both parties submit an invoice for $100 and pay each other, then wait. On the settlement date, the oracle settles the winner's invoice and cancels the loser's. The loser may be unhappy but he lost fair and square.";
					var d = new Date();
                                        document.getElementById( "settlement date" ).value = d.toISOString().substr( 0, 10 );
                                        document.getElementById( "first partys role" ).value = "Gambler";
                                        document.getElementById( "second partys role" ).value = "Gambler";
                                        document.getElementById( "first partys amount" ).value = "100.00";
                                        document.getElementById( "second partys amount" ).value = "100.00";
                                        document.getElementById( "oracle fee" ).value = "1.00";
                                }});
                        </script>
                </body>
    """.format( contract_id_short = contract_id[ 0:10 ] + "...", contract_id=contract_id, allcontracts = allcontractsstring )
    return returnable

@app.route( '/', methods=[ 'POST', 'GET' ] )
def extractor():
    if request.args.get( "id" ) is not None:
        contract_id = request.args.get( "id" )
        con = sqlite3.connect( "contracts.db" )
        cur = con.cursor()
        cur.execute( "SELECT contract from contracts WHERE contract_id = '" + contract_id + "'" )
        contracts = cur.fetchone()
        con.close()
        pricect = json.loads( contracts[ 0 ] )
        pricefeed = requests.get('https://api.kraken.com/0/public/Ticker?pair=XBTUSD')
        krakenprice = pricefeed.json().get( "result" ).get( "XXBTZUSD" ).get( "a" )[ 0 ]
        sats_per_dollar = int( float( "%.8f" % float( 100000000 // int( float ( krakenprice ) ) ) ) )
        server_fee = int( float( pricect[ "oracle_fee" ] ) ) * sats_per_dollar
    if request.args.get( "party" ) == "1" and request.args.get( "id" ) is not None and request.args.get( "processing" ) is not None:
        returnable = "You already submitted an invoice"
        contract_id = request.args.get( "id" )
        con = sqlite3.connect( "contracts.db" )
        cur = con.cursor()
        cur.execute( "SELECT contract from contracts WHERE contract_id = '" + contract_id + "'" )
        contracts = cur.fetchone()
        con.close()
        datum = json.loads( contracts[ 0 ] )
        if str( datum[ "first party hodl invoice" ] ) == "":
            first_party_original_invoice = request.form.get( "invoice" )
            query = ln.PayReqString(
                pay_req=first_party_original_invoice
            )
            response = stub.DecodePayReq( query )
            newexpiry = ( ( response.timestamp + response.expiry ) - int( time.time() ) ) - 5
            first_party_pmthash = str( response.payment_hash )
            amount = response.num_satoshis + server_fee
            first_party_hodl_invoice = getInvoice( newexpiry, first_party_pmthash, amount )
            contract_name = str( datum[ "contract name" ] )
            description = str( datum[ "description" ] )
            first_party_role = str( datum[ "first party role" ] )
            first_party_amount = str( datum[ "first party amount" ] )
            second_party_role = str( datum[ "second party role" ] )
            second_party_amount = str( datum[ "second party amount" ] )
            second_party_original_invoice = str( datum[ "second party original invoice" ] )
            second_party_hodl_invoice = str( datum[ "second party hodl invoice" ] )
            second_party_pmthash = str( datum[ "second party pmthash" ] )
            settlement_date = str( datum[ "settlement date" ] )
            automatic = str( datum[ "automatic" ] )
            btc_price = str( datum[ "btc_price" ] )
            usdt_amount = str( datum[ "usdt_amount" ] )
            usdt_address = str( datum[ "usdt_address" ] )
            oracle_fee = str( datum[ "oracle_fee" ] )
            contract_params = {
                "contract id": contract_id,
                "contract name": contract_name,
                "description": description,
                "first party role": first_party_role,
                "first party amount": first_party_amount,
                "first party original invoice": first_party_original_invoice,
                "first party hodl invoice": first_party_hodl_invoice,
                "first party pmthash": first_party_pmthash,
                "private": 1,
                "second party role": second_party_role,
                "second party amount": second_party_amount,
                "second party original invoice": second_party_original_invoice,
                "second party hodl invoice": second_party_hodl_invoice,
                "second party pmthash": second_party_pmthash,
                "settlement date": settlement_date,
                "automatic": automatic,
                "btc_price": btc_price,
                "usdt_amount": usdt_amount,
                "usdt_address": usdt_address,
                "oracle_fee": oracle_fee
            }
            contract = json.dumps( contract_params )
            con = sqlite3.connect( "contracts.db" )
            cur = con.cursor()
            cur.execute( "UPDATE contracts SET contract = :contract, contract_id = :contract_id, contract_name = :contract_name, description = :description, first_party_role = :first_party_role, first_party_amount = :first_party_amount, first_party_original = :first_party_original, first_party_hodl = :first_party_hodl, first_party_pmthash = :first_party_pmthash, second_party_role = :second_party_role, second_party_amount = :second_party_amount, second_party_original = :second_party_original, second_party_hodl = :second_party_hodl, second_party_pmthash = :second_party_pmthash, settlement_date = :settlement_date, automatic = :automatic, btc_price = :btc_price, usdt_amount = :usdt_amount, usdt_address = :usdt_address, private = :private, oracle_fee = :oracle_fee WHERE contract_id = :contract_id",
                       { "contract": contract, "contract_id": contract_id, "contract_name": contract_name, "description": description, "first_party_role": first_party_role, "first_party_amount": first_party_amount, "first_party_original": "", "first_party_hodl": "", "first_party_pmthash": "", "second_party_role": second_party_role, "second_party_amount": second_party_amount, "second_party_original": "", "second_party_hodl": "", "second_party_pmthash": "", "settlement_date": settlement_date, "automatic": automatic, "btc_price": btc_price, "usdt_amount": usdt_amount, "usdt_address": usdt_address, "private": 0, "oracle_fee": oracle_fee } )
            con.commit()
            returnable = """
                <body style="margin: 0px; font-family: Helvetica, sans-serif;">
                        <div id="header" style="height: 50px; background-color: red;">
                                <h1 style="padding: 7px; color: white;">
                                        Hodl contracts
                                </h1>
                        </div>
                        <div id="leftside" style="position: absolute; left: 0px; top: 50px; background-color: orange; width: 25%; height: 100%;">
                        </div>
                        <div id="middle" style="width: 50%; margin: auto;">
                                <div style="margin: 10px;">
                                        <h2>
                                                Contract {contract_id_short}
                                        </h2>
                                        <p>
						Your submission is being processed. If you are not redirected shortly, <a href="/?id={contract_id}&party={party}">click here</a>
					</p>
                                </div>
                        </div>
                        <div id="rightside" style="position: absolute; right: 0px; top: 50px; background-color: blue; width: 25%; height: 100%;">
                                <div style="margin: 10px; color: white;">
                                </div>
                        </div>
                        <script>
                                function longBars() {{
                                        document.getElementById( "leftside" ).style.height = document.body.offsetHeight + "px";
                                        document.getElementById( "rightside" ).style.height = document.body.offsetHeight + "px";
                                }}
                                longBars();
                        </script>
                        <script>
				setTimeout( function() {{ window.location.href = "/?id={contract_id}&party={party}" }}, 2500 );
                        </script>
                </div>
        """.format( contract_id_short = contract_id[ 0:10 ] + "...", contract_id = contract_id, party = str( request.args.get( "party" ) ) )
        return returnable
    if request.args.get( "party" ) == "1" and request.args.get( "id" ) is not None and request.args.get( "processing" ) is None:
        contract_id = request.args.get( "id" )
        con = sqlite3.connect( "contracts.db" )
        cur = con.cursor()
        cur.execute( "SELECT contract from contracts WHERE contract_id = '" + contract_id + "'" )
        contracts = cur.fetchone()
        con.close()
        datum = json.loads( contracts[ 0 ] )
        contract = json.dumps( datum )
        fpinvoice = str( datum[ "first party hodl invoice" ] )
        spinvoice = str( datum[ "second party hodl invoice" ] )
        p1amt = str( datum[ "first party amount" ] )
        p2amt = str( datum[ "second party amount" ] )
        returnable = """
                <body style="margin: 0px; font-family: Helvetica, sans-serif;">
                        <script src="{qrcodejsfile}"></script>
                        <div id="header" style="height: 50px; background-color: red;">
                                <h1 style="padding: 7px; color: white;">
                                        Hodl contracts
                                </h1>
                        </div>
                        <div id="leftside" style="position: absolute; left: 0px; top: 50px; background-color: orange; width: 25%; height: 100%;">
                        </div>
                        <div id="middle" style="width: 50%; margin: auto;">
                                <div style="margin: 10px;">
                                        <h2>
                                                Contract {contract_id_short}
                                        </h2>
                                        <p id="description">
					</p>
					<form method="post" action="/?processing=true&id={contract_id}&party={party}" style="display: none;">
                                                <p>
                                                        Enter an invoice <span id="invoice amount"></span>
                                                </p>
						<p>
	                                                <input type="text" style="width: 100%; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" id="invoice" name="invoice" placeholder="lnbc1482n0jf9t0wasfjfas9f20fj0fa0...">
						</p>
						<p>
	                                                <button type="submit" style="border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px; cursor: pointer;">Submit</button>
						</p>
					</form>
					<div id="invoice container" style="display: none;">
						Deposit funds to this smart contract<br>
						<a href="lightning:{spinvoice}">
							<div id="invoice div" style="max-width: 300px; margin: auto;">
							</div>
						</a>
					</div>
					<p id="instructions" style="display: none;">
						<span id="instructions if invoiced" style="display: none;">You have already submitted your invoice. </span><span id="instructions if awaiting counterparty invoice" style="display: none;">Please wait while your counterparty creates an invoice. Check back later. </span><span id="instructions if awaiting counterparty deposit" style="display: none;">Please wait while your counterparty pays your invoice. Check back later. </span><span id="instructions if awaiting settlement" style="display: none;">Please await your settlement date (visible in the contract details below) and contact your oracle for more info.</span>
					</p>
					<p id="payment received" style="display: none;">
						You received a payment from your counterparty
					</p>
					<p id="payment sent" style="display: none;">
						Your payment to your counterparty went through
					</p>
					<p id="payment not received" style="display: none;">
						The oracle canceled a payment from your counterparty to you
					</p>
					<p id="payment not sent" style="display: none;">
						The oracle canceled a payment from you to your counterparty
					</p>
					<p id="completion message" style="display: none;">
						This contract is complete
					</p>
					<p id="details button" style="text-decoration: underline; cursor: pointer;" onclick="if ( this.nextElementSibling.style.display != 'none' ) {{this.nextElementSibling.style.display = 'none'; }} else {{this.nextElementSibling.style.display = 'block';}} longBars();">
						View contract details
					</p>
					<p id="details" style="display: none; white-space: pre-wrap; word-wrap: break-word;">
					</p>
                                </div>
                        </div>
                        <div id="rightside" style="position: absolute; right: 0px; top: 50px; background-color: blue; width: 25%; height: 100%;">
                                <div style="margin: 10px; color: white;">
                                </div>
                        </div>
			<script>
				function createQR( data ) {{
                                	var dataUriPngImage = document.createElement( "img" ),
                                	s = QRCode.generatePNG( data, {{
                                	        ecclevel: "M",
                                	        format: "html",
                                	        fillcolor: "#FFFFFF",
                                	        textcolor: "#373737",
                                	        margin: 4,
                                	        modulesize: 8
                                	}});
                                	dataUriPngImage.src = s;
                                	dataUriPngImage.id = "lnurl-auth-image";
					dataUriPngImage.style = "width: 100%;";
					return dataUriPngImage;
                        	}}
			</script>
                        <script>
				function checkStatus( party ) {{
                                        var fpinvoice = "{fpinvoice}";
					var spinvoice = "{spinvoice}";
					var xhttp = new XMLHttpRequest();
					xhttp.onreadystatechange = function() {{
						if ( this.readyState == 4 && this.status == 200 ) {{
							if ( party == 1 ) {{
								if ( xhttp.responseText == "Canceled" ) {{
									document.getElementById( "payment not received" ).style.display = "block";
									document.getElementById( "instructions" ).style.display = "none";
									document.getElementsByTagName( "form" )[ 0 ].style.display = "none";
									document.getElementById( "completion message" ).style.display = "block";
								}}
								if ( xhttp.responseText == "Settled" ) {{
									document.getElementById( "payment received" ).style.display = "block";
									document.getElementById( "instructions" ).style.display = "none";
									document.getElementsByTagName( "form" )[ 0 ].style.display = "none";
									document.getElementById( "completion message" ).style.display = "block";
								}}
							}}
	                                                if ( party == 2 ) {{
								var p1amt = "{p1amt}";
								if ( xhttp.responseText == "No interaction yet" ) {{
									if ( Number( p1amt ) > 0 ) {{
										document.getElementById( "instructions if awaiting counterparty invoice" ).style.display = "inline";
									}} else {{
										document.getElementById( "instructions if awaiting counterparty deposit" ).style.display = "inline";
									}}
									document.getElementById( "instructions if awaiting settlement" ).style.display = "none";
								}}
								if ( xhttp.responseText == "Waiting on other party" && fpinvoice != "" ) {{
									document.getElementById( "instructions" ).style.display = "none";
									document.getElementById( "invoice container" ).style.display = "block";
									if ( !document.getElementById( "invoice div" ).innerHTML.includes( "img" ) ) {{
										if ( spinvoice != "" ) {{
											document.getElementById( "invoice div" ).appendChild( createQR( "{spinvoice}".toUpperCase() ) );
										}} else {{
											window.location.reload();
										}}
									}}
								}} else {{
									document.getElementById( "invoice container" ).style.display = "none";
								}}
								if ( xhttp.responseText == "Contract funded, awaiting settlement" ) {{
									document.getElementById( "instructions if awaiting counterparty invoice" ).style.display = "none";
									document.getElementById( "instructions if awaiting settlement" ).style.display = "inline";
									document.getElementById( "instructions" ).style.display = "block";
								}}
								if ( xhttp.responseText == "Settled" ) {{
									document.getElementById( "payment sent" ).style.display = "block";
									document.getElementById( "instructions" ).style.display = "none";
									document.getElementsByTagName( "form" )[ 0 ].style.display = "none";
									document.getElementById( "completion message" ).style.display = "block";
								}}
								if ( xhttp.responseText == "Canceled" ) {{
									document.getElementById( "payment not sent" ).style.display = "block";
									document.getElementById( "instructions" ).style.display = "none";
									document.getElementsByTagName( "form" )[ 0 ].style.display = "none";
									document.getElementById( "completion message" ).style.display = "block";
								}}
							}}
						}}
					}}
					xhttp.open( "GET", "/checkstatus/?id={contract_id}&party=" + party, true );
					xhttp.send();
				}}
				function loopStatus( party ) {{
					checkStatus( party );
					if ( document.getElementById( "completion message" ).style.display != "block" ) {{
						setTimeout( function() {{ loopStatus( party ); }}, 5000 );
					}}
				}}
				loopStatus( 1 );
				loopStatus( 2 );
                        </script>
                        <script>
                                function longBars() {{
                                        document.getElementById( "leftside" ).style.height = document.body.offsetHeight + "px";
                                        document.getElementById( "rightside" ).style.height = document.body.offsetHeight + "px";
                                }}
                                longBars();
                        </script>
                        <script>
                                json = {contract};
                                document.getElementById( "description" ).innerText = json[ "description" ];
                                document.getElementById( "details" ).innerText = JSON.stringify( json, null, 2 );
                                document.getElementById( "invoice amount" ).innerText = "for $" + json[ "second party amount" ];
				if ( Number( json[ "second party amount" ] ) > 0 && json[ "first party hodl invoice" ] == "" ) {{
					document.getElementsByTagName( "form" )[ 0 ].style.display = "block";
				}}
                                if ( Number( json[ "second party amount" ] ) > 0 && json[ "first party hodl invoice" ] != "" ) {{
					document.getElementById( "instructions if invoiced" ).style.display = "inline";
				}}
                                if ( document.getElementsByTagName( "form" )[ 0 ].style.display == "none" ) {{
					document.getElementById( "instructions" ).style.display = "block";
                                }}
                        </script>
                </div>
        """.format( contract_id_short = contract_id[ 0:10 ] + "...", contract_id = contract_id, contract = contract, party = str( request.args.get( "party" ) ), fpinvoice = fpinvoice, spinvoice = spinvoice, qrcodejsfile = url_for( "static", filename="qrcode.js" ), p1amt = p1amt, p2amt = p2amt )
        return returnable
    if request.args.get( "party" ) == "2" and request.args.get( "id" ) is not None and request.args.get( "processing" ) is not None:
        returnable = "You already submitted an invoice"
        contract_id = request.args.get( "id" )
        con = sqlite3.connect( "contracts.db" )
        cur = con.cursor()
        cur.execute( "SELECT contract from contracts WHERE contract_id = '" + contract_id + "'" )
        contracts = cur.fetchone()
        con.close()
        datum = json.loads( contracts[ 0 ] )
        if str( datum[ "second party hodl invoice" ] ) == "":
            second_party_original_invoice = request.form.get( "invoice" )
            query = ln.PayReqString(
                pay_req=second_party_original_invoice
            )
            response = stub.DecodePayReq( query )
            newexpiry = ( ( response.timestamp + response.expiry ) - int( time.time() ) ) - 5
            second_party_pmthash = str( response.payment_hash )
            amount = response.num_satoshis + server_fee
            second_party_hodl_invoice = getInvoice( newexpiry, second_party_pmthash, amount )
            contract_name = str( datum[ "contract name" ] )
            description = str( datum[ "description" ] )
            first_party_role = str( datum[ "first party role" ] )
            first_party_amount = str( datum[ "first party amount" ] )
            second_party_role = str( datum[ "second party role" ] )
            second_party_amount = str( datum[ "second party amount" ] )
            first_party_original_invoice = str( datum[ "first party original invoice" ] )
            first_party_hodl_invoice = str( datum[ "first party hodl invoice" ] )
            first_party_pmthash = str( datum[ "first party pmthash" ] )
            settlement_date = str( datum[ "settlement date" ] )
            automatic = str( datum[ "automatic" ] )
            btc_price = str( datum[ "btc_price" ] )
            usdt_amount = str( datum[ "usdt_amount" ] )
            usdt_address = str( datum[ "usdt_address" ] )
            oracle_fee = str( datum[ "oracle_fee" ] )
            contract_params = {
                "contract id": contract_id,
                "contract name": contract_name,
                "description": description,
                "first party role": first_party_role,
                "first party amount": first_party_amount,
                "first party original invoice": first_party_original_invoice,
                "first party hodl invoice": first_party_hodl_invoice,
                "first party pmthash": first_party_pmthash,
                "private": 1,
                "second party role": second_party_role,
                "second party amount": second_party_amount,
                "second party original invoice": second_party_original_invoice,
                "second party hodl invoice": second_party_hodl_invoice,
                "second party pmthash": second_party_pmthash,
                "settlement date": settlement_date,
                "automatic": automatic,
                "btc_price": btc_price,
                "usdt_amount": usdt_amount,
                "usdt_address": usdt_address,
                "oracle_fee": oracle_fee
            }
            contract = json.dumps( contract_params )
            con = sqlite3.connect( "contracts.db" )
            cur = con.cursor()
            cur.execute( "UPDATE contracts SET contract = :contract, contract_id = :contract_id, contract_name = :contract_name, description = :description, first_party_role = :first_party_role, first_party_amount = :first_party_amount, first_party_original = :first_party_original, first_party_hodl = :first_party_hodl, first_party_pmthash = :first_party_pmthash, second_party_role = :second_party_role, second_party_amount = :second_party_amount, second_party_original = :second_party_original, second_party_hodl = :second_party_hodl, second_party_pmthash = :second_party_pmthash, settlement_date = :settlement_date, automatic = :automatic, btc_price = :btc_price, usdt_amount = :usdt_amount, usdt_address = :usdt_address, private = :private, oracle_fee = :oracle_fee WHERE contract_id = :contract_id",
                       { "contract": contract, "contract_id": contract_id, "contract_name": contract_name, "description": description, "first_party_role": first_party_role, "first_party_amount": first_party_amount, "first_party_original": "", "first_party_hodl": "", "first_party_pmthash": "", "second_party_role": second_party_role, "second_party_amount": second_party_amount, "second_party_original": "", "second_party_hodl": "", "second_party_pmthash": "", "settlement_date": settlement_date, "automatic": automatic, "btc_price": btc_price, "usdt_amount": usdt_amount, "usdt_address": usdt_address, "private": 0, "oracle_fee": oracle_fee } )
            con.commit()
            returnable = """
                <body style="margin: 0px; font-family: Helvetica, sans-serif;">
                        <div id="header" style="height: 50px; background-color: red;">
                                <h1 style="padding: 7px; color: white;">
                                        Hodl contracts
                                </h1>
                        </div>
                        <div id="leftside" style="position: absolute; left: 0px; top: 50px; background-color: orange; width: 25%; height: 100%;">
                        </div>
                        <div id="middle" style="width: 50%; margin: auto;">
                                <div style="margin: 10px;">
                                        <h2>
                                                Contract {contract_id_short}
                                        </h2>
                                        <p>
						Your submission is being processed. If you are not redirected shortly, <a href="/?id={contract_id}&party={party}">click here</a>
					</p>
                                </div>
                        </div>
                        <div id="rightside" style="position: absolute; right: 0px; top: 50px; background-color: blue; width: 25%; height: 100%;">
                                <div style="margin: 10px; color: white;">
                                </div>
                        </div>
                        <script>
                                function longBars() {{
                                        document.getElementById( "leftside" ).style.height = document.body.offsetHeight + "px";
                                        document.getElementById( "rightside" ).style.height = document.body.offsetHeight + "px";
                                }}
                                longBars();
                        </script>
                        <script>
				setTimeout( function() {{ window.location.href = "/?id={contract_id}&party={party}" }}, 2500 );
                        </script>
                </div>
        """.format( contract_id_short = contract_id[ 0:10 ] + "...", contract_id = contract_id, party = str( request.args.get( "party" ) ) )
        return returnable
    if request.args.get( "party" ) == "2" and request.args.get( "id" ) is not None and request.args.get( "processing" ) is None:
        contract_id = request.args.get( "id" )
        con = sqlite3.connect( "contracts.db" )
        cur = con.cursor()
        cur.execute( "SELECT contract from contracts WHERE contract_id = '" + contract_id + "'" )
        contracts = cur.fetchone()
        con.close()
        datum = json.loads( contracts[ 0 ] )
        contract = json.dumps( datum )
        fpinvoice = str( datum[ "first party hodl invoice" ] );
        spinvoice = str( datum[ "second party hodl invoice" ] );
        p1amt = str( datum[ "first party amount" ] )
        p2amt = str( datum[ "second party amount" ] )
        returnable = """
                <body style="margin: 0px; font-family: Helvetica, sans-serif;">
                        <script src="{qrcodejsfile}"></script>
                        <div id="header" style="height: 50px; background-color: red;">
                                <h1 style="padding: 7px; color: white;">
                                        Hodl contracts
                                </h1>
                        </div>
                        <div id="leftside" style="position: absolute; left: 0px; top: 50px; background-color: orange; width: 25%; height: 100%;">
                        </div>
                        <div id="middle" style="width: 50%; margin: auto;">
                                <div style="margin: 10px;">
                                        <h2>
                                                Contract {contract_id_short}
                                        </h2>
                                        <p id="description">
					</p>
					<form method="post" action="/?processing=true&id={contract_id}&party={party}" style="display: none;">
                                                <p>
                                                        Enter an invoice <span id="invoice amount"></span>
                                                </p>
						<p>
	                                                <input type="text" style="width: 100%; border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px;" id="invoice" name="invoice" placeholder="lnbc1482n0jf9t0wasfjfas9f20fj0fa0...">
						</p>
						<p>
	                                                <button type="submit" style="border: 2px solid black; border-radius: 5px; height: 40px; font-size: 18px; cursor: pointer;">Submit</button>
						</p>
					</form>
					<div id="invoice container" style="display: none;">
						Deposit funds to this smart contract<br>
						<a href="lightning:{fpinvoice}">
							<div id="invoice div" style="max-width: 300px; margin: auto;">
							</div>
						</a>
					</div>
					<p id="instructions" style="display: none;">
						<span id="instructions if invoiced" style="display: none;">You have already submitted your invoice. </span><span id="instructions if awaiting counterparty invoice" style="display: none;">Please wait while your counterparty creates an invoice. Check back later. </span><span id="instructions if awaiting counterparty deposit" style="display: none;">Please wait while your counterparty pays your invoice. Check back later. </span><span id="instructions if awaiting settlement" style="display: none;">Please await your settlement date (visible in the contract details below) and contact your oracle for more info.</span>
					</p>
					<p id="payment received" style="display: none;">
						You received a payment from your counterparty
					</p>
					<p id="payment sent" style="display: none;">
						Your payment to your counterparty went through
					</p>
					<p id="payment not received" style="display: none;">
						The oracle canceled a payment from your counterparty to you
					</p>
					<p id="payment not sent" style="display: none;">
						The oracle canceled a payment from you to your counterparty
					</p>
					<p id="completion message" style="display: none;">
						This contract is complete
					</p>
					<p id="details button" style="text-decoration: underline; cursor: pointer;" onclick="if ( this.nextElementSibling.style.display != 'none' ) {{this.nextElementSibling.style.display = 'none'; }} else {{this.nextElementSibling.style.display = 'block';}} longBars();">
						View contract details
					</p>
					<p id="details" style="display: none; white-space: pre-wrap; word-wrap: break-word;">
					</p>
                                </div>
                        </div>
                        <div id="rightside" style="position: absolute; right: 0px; top: 50px; background-color: blue; width: 25%; height: 100%;">
                                <div style="margin: 10px; color: white;">
                                </div>
                        </div>
			<script>
				function createQR( data ) {{
                                	var dataUriPngImage = document.createElement( "img" ),
                                	s = QRCode.generatePNG( data, {{
                                	        ecclevel: "M",
                                	        format: "html",
                                	        fillcolor: "#FFFFFF",
                                	        textcolor: "#373737",
                                	        margin: 4,
                                	        modulesize: 8
                                	}});
                                	dataUriPngImage.src = s;
                                	dataUriPngImage.id = "lnurl-auth-image";
					dataUriPngImage.style = "width: 100%;";
					return dataUriPngImage;
                        	}}
			</script>
                        <script>
				function checkStatus( party ) {{
					var fpinvoice = "{fpinvoice}";
                                        var spinvoice = "{spinvoice}";
					var xhttp = new XMLHttpRequest();
					xhttp.onreadystatechange = function() {{
						if ( this.readyState == 4 && this.status == 200 ) {{
							if ( party == 2 ) {{
								if ( xhttp.responseText == "Canceled" ) {{
									document.getElementById( "payment not received" ).style.display = "block";
									document.getElementById( "instructions" ).style.display = "none";
									document.getElementsByTagName( "form" )[ 0 ].style.display = "none";
									document.getElementById( "completion message" ).style.display = "block";
								}}
								if ( xhttp.responseText == "Settled" ) {{
									document.getElementById( "payment received" ).style.display = "block";
									document.getElementById( "instructions" ).style.display = "none";
									document.getElementsByTagName( "form" )[ 0 ].style.display = "none";
									document.getElementById( "completion message" ).style.display = "block";
								}}
							}}
	                                                if ( party == 1 ) {{
								var p2amt = "{p2amt}";
								if ( xhttp.responseText == "No interaction yet" ) {{
									if ( Number( p2amt ) > 0 ) {{
										document.getElementById( "instructions if awaiting counterparty invoice" ).style.display = "inline";
									}} else {{
										document.getElementById( "instructions if awaiting counterparty deposit" ).style.display = "inline";
									}}
									document.getElementById( "instructions if awaiting settlement" ).style.display = "none";
								}}
								if ( xhttp.responseText == "Waiting on other party" && spinvoice != "" ) {{
									document.getElementById( "instructions" ).style.display = "none";
									document.getElementById( "invoice container" ).style.display = "block";
									if ( !document.getElementById( "invoice div" ).innerHTML.includes( "img" ) ) {{
										if ( fpinvoice != "" ) {{
											document.getElementById( "invoice div" ).appendChild( createQR( "{fpinvoice}".toUpperCase() ) );
										}} else {{
											window.location.reload();
										}}
									}}
								}} else {{
									document.getElementById( "invoice container" ).style.display = "none";
								}}
								if ( xhttp.responseText == "Contract funded, awaiting settlement" ) {{
									document.getElementById( "instructions if awaiting counterparty invoice" ).style.display = "none";
									document.getElementById( "instructions if awaiting settlement" ).style.display = "inline";
									document.getElementById( "instructions" ).style.display = "block";
								}}
								if ( xhttp.responseText == "Settled" ) {{
									document.getElementById( "payment sent" ).style.display = "block";
									document.getElementById( "instructions" ).style.display = "none";
									document.getElementsByTagName( "form" )[ 0 ].style.display = "none";
									document.getElementById( "completion message" ).style.display = "block";
								}}
								if ( xhttp.responseText == "Canceled" ) {{
									document.getElementById( "payment not sent" ).style.display = "block";
									document.getElementById( "instructions" ).style.display = "none";
									document.getElementsByTagName( "form" )[ 0 ].style.display = "none";
									document.getElementById( "completion message" ).style.display = "block";
								}}
							}}
						}}
					}}
					xhttp.open( "GET", "/checkstatus/?id={contract_id}&party=" + party, true );
					xhttp.send();
				}}
				function loopStatus( party ) {{
					checkStatus( party );
					if ( document.getElementById( "completion message" ).style.display != "block" ) {{
						setTimeout( function() {{ loopStatus( party ); }}, 5000 );
					}}
				}}
				loopStatus( 1 );
				loopStatus( 2 );
                        </script>
                        <script>
                                function longBars() {{
                                        document.getElementById( "leftside" ).style.height = document.body.offsetHeight + "px";
                                        document.getElementById( "rightside" ).style.height = document.body.offsetHeight + "px";
                                }}
                                longBars();
                        </script>
                        <script>
                                json = {contract};
                                document.getElementById( "description" ).innerText = json[ "description" ];
                                document.getElementById( "details" ).innerText = JSON.stringify( json, null, 2 );
                                document.getElementById( "invoice amount" ).innerText = "for $" + json[ "first party amount" ];
				if ( Number( json[ "first party amount" ] ) > 0 && json[ "second party hodl invoice" ] == "" ) {{
					document.getElementsByTagName( "form" )[ 0 ].style.display = "block";
				}}
                                if ( Number( json[ "first party amount" ] ) > 0 && json[ "second party hodl invoice" ] != "" ) {{
					document.getElementById( "instructions if invoiced" ).style.display = "inline";
				}}
                                if ( document.getElementsByTagName( "form" )[ 0 ].style.display == "none" ) {{
					document.getElementById( "instructions" ).style.display = "block";
                                }}
                        </script>
                </div>
        """.format( contract_id_short = contract_id[ 0:10 ] + "...", contract_id = contract_id, contract = contract, party = str( request.args.get( "party" ) ), fpinvoice = fpinvoice, spinvoice = spinvoice, qrcodejsfile = url_for( "static", filename="qrcode.js" ), p1amt = p1amt, p2amt = p2amt )
        return returnable
    return ""
"""
@app.route( '/check/', methods=[ 'POST', 'GET' ] )
def retriever():
    from flask import request
    if request.args.get( "pmthash" ):
        pmthash = request.args.get( "pmthash" )
        request = ln.PaymentHash(
            r_hash_str=pmthash
        )
        response = stub.LookupInvoice( request )
        status = response.state
        returnable = "The other party didn't pay yet"
        if status == 3:
            paidscript = hcconditions.is2even()
            if paidscript == 1:
                payFirstParty( pmthash )
            else:
                paySecondParty( pmthash )
        return returnable
#    return json.dumps( response )
"""
if __name__ == '__main__':
    app.run()
