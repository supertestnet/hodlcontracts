import rpc_pb2 as ln
import rpc_pb2_grpc as lnrpc
import invoices_pb2 as invoicesrpc
import invoices_pb2_grpc as invoicesstub
import router_pb2 as routerrpc
import router_pb2_grpc as routerstub
import grpc
import os
import codecs
import json
import time
import sqlite3
import hcconditions
from stem.control import Controller
from flask import Flask, redirect, url_for, request

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
    stub2 = invoicesstub.InvoicesStub( channel )
    request = invoicesrpc.SettleInvoiceMsg(
        preimage=preimage.decode( "hex" )
    )
    return stub2.SettleInvoice( request )

app = Flask(__name__)

@app.route( '/', methods=[ 'POST', 'GET' ] )
def extractor():
    if request.args.get( "user" ) == "alice":
        returnable = '<form method="post"><p>Enter your invoice</p><p><input type="text" name="invoice"></p><p><input type="submit" value="Submit"></p>'
        if request.form.get( "invoice" ):
            original_invoice = request.form.get( "invoice" )
            query = ln.PayReqString(
                pay_req=original_invoice
            )
            response = stub.DecodePayReq( query )
            newexpiry = ( ( response.timestamp + response.expiry ) - int( time.time() ) ) - 5
            pmthash = str( response.payment_hash )
            amount = response.num_satoshis + 1
            hodl_invoice = getInvoice( newexpiry, pmthash, amount )
            call = "is2even"
            contract_params = {
                "first party original invoice": original_invoice,
                "first party hodl invoice": hodl_invoice,
                "first party pmthash": pmthash,
                "private": 0,
                "second party original invoice": "",
                "second party hodl invoice": "",
                "second party pmthash": "",
                "call": call
            }
            contract = json.dumps( contract_params )
            con = sqlite3.connect( "contracts.db" )
            cur = con.cursor()
            cur.execute( """CREATE TABLE IF NOT EXISTS contracts (
                        contract text,
                        first_party_original text,
                        first_party_hodl text,
                        second_party_original text,
                        second_party_hodl text,
                        first_party_pmthash text,
                        second_party_pmthash text,
                        call text,
                        private integer
                        )""" )
            con.commit()
            cur.execute( "INSERT INTO contracts VALUES ( :contract, :first_party_original, :first_party_hodl, :second_party_original, :second_party_hodl, :first_party_pmthash, :second_party_pmthash, :call, :private )",
                       { "contract": contract, "first_party_original": original_invoice, "first_party_hodl": hodl_invoice, "second_party_original": "", "second_party_hodl": "", "first_party_pmthash": pmthash, "second_party_pmthash": "", "call": call, "private": 0 } )
            con.commit()
            cur.execute( "SELECT * from contracts WHERE first_party_pmthash = '" + pmthash + "'" )
            contracts = cur.fetchone()
            con.close()
            returnable = json.dumps( contracts )
        return returnable
    if request.args.get( "user" ) == "bob":
        if request.args.get( "pmthash" ) is not None:
            pmthash = request.args.get( "pmthash" )
            con = sqlite3.connect( "contracts.db" )
            cur = con.cursor()
            cur.execute( "SELECT contract from contracts WHERE first_party_pmthash = '" + pmthash + "'" )
            contracts = cur.fetchone()
            con.close()
            results = ''.join( contracts )
            datum = json.loads( results )
            returnable = str( datum[ "first party hodl invoice" ] )
#            returnable = json.dumps( contracts )
            return returnable
        else:
            con = sqlite3.connect( "contracts.db" )
            cur = con.cursor()
            cur.execute( "SELECT * from contracts" )
            contracts = cur.fetchall()
            con.close()
            results = []
            for row in contracts:
#                results.append( json.dumps( row ) )
#                results += json.dumps( row )
#                results += str( row )
                results.append( row )
#            results = ''.join( contracts )
            datum = json.loads( results[ 0 ][ 0 ] )
            returnable = json.dumps( datum )
            returnable += '<form method="post"><p>Enter your invoice</p><p><input type="text" name="invoice"></p><p><input type="submit" value="Submit"></p>'
            if request.form.get( "invoice" ):
                original_invoice = request.form.get( "invoice" )
                query = ln.PayReqString(
                    pay_req=original_invoice
                )
                response = stub.DecodePayReq( query )
                newexpiry = ( ( response.timestamp + response.expiry ) - int( time.time() ) ) - 5
                pmthash = str( response.payment_hash )
                amount = response.num_satoshis + 1
                hodl_invoice = getInvoice( newexpiry, pmthash, amount )
                first_party_original_invoice = datum[ "first party original invoice" ]
                first_party_hodl_invoice = datum[ "first party hodl invoice" ]
                first_party_pmthash = datum[ "first party pmthash" ]
                call = datum[ "call" ]
#                datum[ "second party hodl invoice" ] = "test"
                contract_params = {
                    "first party original invoice": first_party_original_invoice,
                    "first party hodl invoice": first_party_hodl_invoice,
                    "first party pmthash": first_party_pmthash,
                    "private": 0,
                    "second party original invoice": original_invoice,
                    "second party hodl invoice": hodl_invoice,
                    "second party pmthash": pmthash,
                    "call": call
                }
                contract = json.dumps( contract_params )
                con = sqlite3.connect( "contracts.db" )
                cur = con.cursor()
                cur.execute( "UPDATE contracts SET contract = :contract, first_party_original = :first_party_original, first_party_hodl = :first_party_hodl, second_party_original = :second_party_original, second_party_hodl = :second_party_hodl, first_party_pmthash = :first_party_pmthash, second_party_pmthash = :second_party_pmthash, call = :call, private = :private WHERE first_party_pmthash = :first_party_pmthash",
                           { "contract": contract, "first_party_original": first_party_original_invoice, "first_party_hodl": first_party_hodl_invoice, "second_party_original": original_invoice, "second_party_hodl": hodl_invoice, "first_party_pmthash": first_party_pmthash, "second_party_pmthash": pmthash, "call": call, "private": 0 } )
                con.commit()
                cur.execute( "SELECT * from contracts WHERE first_party_pmthash = '" + pmthash + "'" )
                contracts = cur.fetchone()
                con.close()
                returnable = json.dumps( contracts )
            return returnable
    return ""

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
#        status = str( response.settled )
#	return str( dir( response ) )
#        prestatus = str( response )
#        status = prestatus[ prestatus.find( "state: " ) + 6:prestatus.find( "htlcs {" ) ]
#        status = ''.join( [ i for i in status if i.isalpha() ] )
#        returnable = status
#        if status == "True": <-- this is what the status says if you query response.settled
        returnable = "Bob didn't pay yet"
        if status == 3:
            paidscript = hcconditions.is2even()
            if paidscript != 1:
                returnable = "The script returned false"
            else:
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
        return returnable
#    return json.dumps( response )

if __name__ == '__main__':
    app.run()
