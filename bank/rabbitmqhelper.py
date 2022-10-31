from datetime import datetime
import queue
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()


def transactionMessageParser(
    txid, sender_account, sender_rmn, reciever_account, amount, date: datetime
):
    return {
        "txid": txid,
        "sender_account": sender_account,
        "sender_rmn": sender_rmn,
        "reciever_account": reciever_account,
        "amount": amount,
        "date": date.strftime("%d-%m-%Y"),
    }


def periodicBalanceParser(rmn, account_number, balance, status):
    return {
        "rmn": rmn,
        "account_number": account_number,
        "balance": balance,
        "status": status,
    }


def miniStatementParser(data):
    output = []
    for i in data:
        output.append(
            {
                "txid": i["txid"],
                "sender": i["sender"],
                "reciever": i["reciever"],
                "amount": i["amount"],
                "time_stamp": i["time_stamp"][:10][::-1],
            }
        )

    return output


def pushMessagePost(message, message_type):
    queue = channel.queue_declare("push")
    exchange = channel.exchange_declare("bank", exchange_type="direct")
    channel.basic_publish(
        exchange="bank",
        routing_key="push",
        body=str({"type": message_type, "data": message}),
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ),
    )


def pullMessagePost(message, email, message_type):
    queue = channel.queue_declare("pull")
    exchange = channel.exchange_declare("bank")
    channel.basic_publish(
        exchange="bank",
        routing_key="pull",
        body=str({"type": message_type, "email": email, "data": message}),
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ),
    )
