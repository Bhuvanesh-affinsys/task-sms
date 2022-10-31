from curses import ALL_MOUSE_EVENTS
from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.
import pika
from .rabbitmqhelper import pushMessagePost, transactionMessageParser


def nonNegativeNumberValidator(value):
    if not value >= 0:
        raise ValidationError


class InsufficientBalance(Exception):
    def __init__(self):
        self.message = "Insufficient balance"


class Customer(models.Model):
    cif = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    rmn = models.CharField(max_length=10)
    email = models.EmailField(max_length=254)
    joined_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"firstname: {self.first_name} lastname: {self.last_name} cif : {self.cif}"
        )


class Account(models.Model):
    account_number = models.AutoField(primary_key=True)
    cif_fk = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="cif_fk"
    )
    balance = models.IntegerField(validators=[nonNegativeNumberValidator])
    status = models.CharField(max_length=20)
    description = models.CharField(max_length=30)
    opened_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"account_number: {self.account_number} cif: {self.cif_fk} balance: {self.balance} type: {self.status} description: {self.description}"


class Ledger(models.Model):
    txid = models.AutoField(primary_key=True)
    sender = models.ForeignKey(
        Account, on_delete=models.RESTRICT, related_name="sender"
    )
    reciever = models.ForeignKey(
        Account, on_delete=models.RESTRICT, related_name="reciever"
    )
    amount = models.IntegerField(validators=[nonNegativeNumberValidator])
    time_stamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.sender.balance - self.amount < 0 or self.amount == 0:
            raise InsufficientBalance()
        else:
            self.sender.balance -= self.amount
            self.reciever.balance += self.amount
            self.sender.save()
            self.reciever.save()
            super().save(*args, **kwargs)
            pushMessagePost(
                transactionMessageParser(
                    txid=self.txid,
                    sender_account=self.sender.account_number,
                    sender_rmn=self.sender.cif_fk.rmn,
                    reciever_account=self.reciever.account_number,
                    amount=self.amount,
                    date=self.time_stamp.date(),
                ),
                message_type="transaction",
            )

    def __str__(self):
        return f"id: {self.txid} sender: {self.sender} reciever : {self.reciever} amount: {self.amount} time_stamp: {self.time_stamp}"
