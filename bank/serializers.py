from dataclasses import fields
from rest_framework.serializers import ModelSerializer

from bank.models import Account, Ledger


class LedgerSerializer(ModelSerializer):
    class Meta:
        model = Ledger
        fields = ["txid", "sender", "reciever", "amount", "time_stamp"]


class AccountBalanceSerializer(ModelSerializer):
    class Meta:
        model = Account
        fields = ["account_number", "cif_fk", "balance", "status"]
