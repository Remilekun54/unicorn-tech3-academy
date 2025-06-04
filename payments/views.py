import stripe
import uuid
import json

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic.base import TemplateView

from django.contrib import messages

from django.http import JsonResponse

import gopay
from gopay.enums import Recurrence, PaymentInstrument, BankSwiftCode, Currency, Language

from payments.forms import AmountForm
from .models import Invoice

from paystackapi.transaction import Transaction


def payment_paypal(request):
    return render(request, "payments/paypal.html", context={})


def payment_stripe(request):
    return render(request, "payments/stripe.html", context={})


def payment_coinbase(request):
    return render(request, "payments/coinbase.html", context={})


def payment_paylike(request):
    return render(request, "payments/paylike.html", context={})


def payment_succeed(request):
    return render(request, "payments/payment_succeed.html", context={})


class PaymentGetwaysView(TemplateView):
    template_name = "payments/payment_gateways.html"

    def get_context_data(self, **kwargs):
        context = super(PaymentGetwaysView, self).get_context_data(**kwargs)
        context["key"] = settings.STRIPE_PUBLISHABLE_KEY
        context["amount"] = 500
        context["description"] = "Stripe Payment"
        context["invoice_session"] = self.request.session["invoice_session"]
        print(context["invoice_session"])
        return context


def stripe_charge(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if request.method == "POST":
        charge = stripe.Charge.create(
            amount=500,
            currency="eur",
            description="A Django charge",
            source=request.POST["stripeToken"],
        )
        invoice_code = request.session["invoice_session"]
        invoice = Invoice.objects.get(invoice_code=invoice_code)
        invoice.payment_complete = True
        invoice.save()
        return redirect("completed")
        # return JsonResponse({"invoice_code": invoice.invoice_code}, status=201)
        # return render(request, 'payments/charge.html')


def gopay_charge(request):
    if request.method == "POST":
        user = request.user

        payments = gopay.payments(
            {
                "goid": "[PAYMENT_ID]",
                "clientId": "[GOPAY_CLIENT_ID]",
                "clientSecret": "[GOPAY_CLIENT_SECRET]",
                "isProductionMode": False,
                "scope": gopay.TokenScope.ALL,
                "language": gopay.Language.ENGLISH,
                "timeout": 30,
            }
        )

        # recurrent payment must have field ''
        recurrentPayment = {
            "recurrence": {
                "recurrence_cycle": Recurrence.DAILY,
                "recurrence_period": "7",
                "recurrence_date_to": "2015-12-31",
            }
        }

        # pre-authorized payment must have field 'preauthorization'
        preauthorizedPayment = {"preauthorization": True}

        response = payments.create_payment(
            {
                "payer": {
                    "default_payment_instrument": PaymentInstrument.BANK_ACCOUNT,
                    "allowed_payment_instruments": [PaymentInstrument.BANK_ACCOUNT],
                    "default_swift": BankSwiftCode.FIO_BANKA,
                    "allowed_swifts": [BankSwiftCode.FIO_BANKA, BankSwiftCode.MBANK],
                    "contact": {
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone_number": user.phone,
                        "city": "example city",
                        "street": "Plana 67",
                        "postal_code": "373 01",
                        "country_code": "CZE",
                    },
                },
                "amount": 150,
                "currency": Currency.CZECH_CROWNS,
                "order_number": "001",
                "order_description": "pojisteni01",
                "items": [
                    {"name": "item01", "amount": 50},
                    {"name": "item02", "amount": 100},
                ],
                "additional_params": [{"name": "invoicenumber", "value": "2015001003"}],
                "callback": {
                    "return_url": "http://www.your-url.tld/return",
                    "notification_url": "http://www.your-url.tld/notify",
                },
                "lang": Language.CZECH,  # if lang is not specified, then default lang is used
            }
        )

        if response.has_succeed():
            print("\nPayment Succeed\n")
            print("hooray, API returned " + str(response))
        else:
            print("\nPayment Fail\n")
            print(
                "oops, API returned " + str(response.status_code) + ": " + str(response)
            )
        return JsonResponse({"message": str(response)})

    return JsonResponse({"message": "GET requested"})


def paymentComplete(request):
    print(request.is_ajax())
    if request.is_ajax() or request.method == "POST":
        invoice_id = request.session["invoice_session"]
        invoice = Invoice.objects.get(id=invoice_id)
        invoice.payment_complete = True
        invoice.save()
        # return redirect('invoice', invoice.invoice_code)
    body = json.loads(request.body)
    print("BODY:", body)
    return JsonResponse("Payment completed!", safe=False)


def create_invoice(request):
    print(request.is_ajax())
    if request.method == "POST":
        invoice = Invoice.objects.create(
            user=request.user,
            amount=request.POST.get("amount"),
            total=26,
            invoice_code=str(uuid.uuid4()),
        )
        request.session["invoice_session"] = invoice.invoice_code
        return redirect("payment_gateways")
    # if request.is_ajax():
    #     invoice = Invoice.objects.create(
    #         user = request.user,
    #         amount = 15,
    #         total=26,
    #     )
    #     return JsonResponse({'invoice': invoice}, status=201) # created

    return render(
        request,
        "invoices.html",
        context={"invoices": Invoice.objects.filter(user=request.user)},
    )


def invoice_detail(request, slug):
    return render(
        request,
        "invoice_detail.html",
        context={"invoice": Invoice.objects.get(invoice_code=slug)},
    )


"""
Handle Paystack Redirect After Payment
Configure Paystack Webhook URL

In your Paystack dashboard, set the callback URL to:

- https://yourdomain.com/paystack/verify/

This ensures Paystack redirects the user after payment.
"""


def payment_paystack(request):
    if request.method == 'POST':
        form = AmountForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            reference = str(uuid.uuid4())

            # Initialize transaction with Paystack
            response = Transaction.initialize(
                reference=reference,
                amount=int(amount * 100),  # Convert to kobo
                email=request.user.email,
                subaccount="ACCT_xxxxxxxxxxxxxxx",  # Receiver's Paystack subaccount
                bearer="subaccount"  # Ensures the receiver gets the full amount
            )

            if response.get('status'):
                # Store transaction reference in session for later verification
                request.session["transaction_reference"] = reference
                request.session["payment_amount"] = float(amount)

                # Redirect to Paystack authorization URL
                return HttpResponseRedirect(response['data']['authorization_url'])
            else:
                messages.error(request, "Transaction initialization failed. Please try again.")
                return JsonResponse(response, status=400)

    else:
        form = AmountForm()

    return render(request, "payments/custom_payment.html", {"form": form})


def verify_payment(request):
    reference = request.GET.get("reference")  # Get reference from Paystack callback
    transaction_reference = request.session.get("transaction_reference")
    amount = request.session.get("payment_amount")

    if not reference or reference != transaction_reference:
        messages.error(request, "Invalid transaction reference.")
        return redirect("payment_failed")

    # Verify transaction with Paystack
    response = Transaction.verify(reference)

    if response.get("status") and response["data"]["status"] == "success":
        # Payment successful, save invoice
        invoice = Invoice.objects.create(
            user=request.user,
            amount=amount,
            total=amount + 26,  # Assuming 26 is a processing fee
            invoice_code=transaction_reference,
        )
        
        # Cleanup session data
        del request.session["transaction_reference"]
        del request.session["payment_amount"]

        messages.success(request, f"Payment of {amount} Naira was successful.")
        return redirect("payment_success")  # Redirect to a success page
    else:
        messages.error(request, "Payment verification failed.")
        return redirect("payment_failed")