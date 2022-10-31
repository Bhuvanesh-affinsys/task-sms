from django.shortcuts import render

from rest_framework import response, request

from rest_framework.generics import ListAPIView, RetrieveAPIView

from rest_framework.views import APIView

from rest_framework.parsers import FormParser

from bank.models import Account, Ledger
from bank.rabbitmqhelper import (
    pushMessagePost,
    periodicBalanceParser,
    pullMessagePost,
    miniStatementParser,
)
from bank.serializers import AccountBalanceSerializer, LedgerSerializer

# Create your views here.


class TransactionalListView(ListAPIView):
    model = Ledger
    queryset = Ledger.objects.filter()
    serializer_class = LedgerSerializer

    def list(self, request: request.Request, **kwargs):
        account_number = request.query_params["account_number"]
        query_set = Ledger.objects.filter(
            sender__account_number=account_number
        ).order_by("-time_stamp")
        serializer = LedgerSerializer(query_set, many=True)
        return response.Response(serializer.data)


class AccountBalanceRetrieve(RetrieveAPIView):
    model = Account
    queryset = Account.objects.filter()
    serializer_class = AccountBalanceSerializer

    def retrieve(self, request: request.Request, **kwargs):
        query_set = Account.objects.all()
        serializer = AccountBalanceSerializer(query_set, many=True)
        for account in query_set:
            pushMessagePost(
                message=periodicBalanceParser(
                    account.cif_fk.rmn,
                    account.account_number,
                    account.balance,
                    account.status,
                ),
                message_type="periodicbalance",
            )
        return response.Response(serializer.data)


class MiniStatementView(APIView):
    model = Account
    queryset = Account.objects.filter()
    serializer_class = AccountBalanceSerializer
    parser_classes = [FormParser]

    def get(self, request, *args, **kwargs):
        account_number = request.query_params["account_number"]
        print(request.data)
        last_five_trans = LedgerSerializer(
            Ledger.objects.filter(sender=account_number).order_by("-time_stamp")[:5],
            many=True,
        )
        pullMessagePost(
            miniStatementParser(last_five_trans.data),
            Account.objects.filter(account_number=account_number).get().cif_fk.email,
            message_type="ministatement",
        )
        return response.Response(str(last_five_trans.data))
