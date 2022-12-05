import json
import logging
import uuid

import requests

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def generate_uuid():
    uid = str(uuid.uuid4())
    return uid


def get_access_token(session_token: str):
    LOGGER.debug("Getting access token...")
    try:
        session = requests.Session()
        session.cookies.set("__Secure-next-auth.session-token", session_token)
        response = session.get("https://chat.openai.com/api/auth/session")
        response.raise_for_status()

        access_token = response.json()["accessToken"]
        LOGGER.debug("Access token: ", access_token)
        return access_token
    except Exception as e:
        LOGGER.exception(e)
        raise


class ChatBot:
    def __init__(self, session_token):
        self.session_token = session_token
        self.headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + get_access_token(session_token),
            "Content-Type": "application/json",
        }
        self.conversation_id = None
        self.parent_id = generate_uuid()

    def get_chat_response(self, prompt) -> dict:
        data = {
            "action": "next",
            "messages": [
                {
                    "id": str(generate_uuid()),
                    "role": "user",
                    "content": {"content_type": "text", "parts": [prompt]},
                }
            ],
            "conversation_id": self.conversation_id,
            "parent_message_id": self.parent_id,
            "model": "text-davinci-002-render",
        }
        response = requests.post(
            "https://chat.openai.com/backend-api/conversation",
            headers=self.headers,
            data=json.dumps(data),
        )
        # json_data = response.json()
        # print(f"json_data: {json_data}")
        try:
            response = response.text.splitlines()[-4]
            response = response[6:]
        except:
            raise
        response = json.loads(response)
        self.parent_id = response["message"]["id"]
        self.conversation_id = response["conversation_id"]
        message = response["message"]["content"]["parts"][0]
        return {
            "message": message,
            "conversation_id": self.conversation_id,
            "parent_id": self.parent_id,
        }


cb = ChatBot(
    "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..qjVLI7kf0Ya_qcUg.csjbWEI-Lic2E-0YeK8hWH13AJkDcCSJTRQQ_e4VdL8Y9YLuVuOwLLZCH28QHuZcg30i8EmvhSgUs8KaBC9WdMvvamcjyY96eYa8DEJd1qfEec4KzY-l6PVg3PrST0Ve5F2OpbgGdLcfGFMtIRc-F0UQ4jRptqrTo8hJljlSeCObOkXWihiDFF_JMTMDv2a3E4-pCSM2NRTZmBclD1aCUt5e3myAeJVOnqQIqz561RNuvmsJl6zO_u6thvu86FfoRY-5xYgeAEDKxHnXKOz5SMkz7NhzujqaPgYNXp8s-E4wb7rLS6vyixB_qcpmKLyRscqNhLEmiofooq1A1GL37r7aH6_tRdlI1NMwYpLkcypbeVO1WA2u1AUXAA9FWNbsRscxdCEuxbxVz3DZLaGR0Kp1gRISXPNKZGvldMY8e5ncPmfB8dqijvGVIoK-Eo9O-SbyPZsYLvyvI85mlUGmoHwmAryuricVMKgmkrFEPRcxwvPy9JeEORvwfstZjrO8lhSGri344JIpU0Q35zxZc98IErxNiMb-pCxDvvhTgZ9bic-SXSTCUDK7XQdK5YcO4X1T0v--2-6A1Iv54zD6QALE51axnYjum7IyRPRyYTTmzJUYl2YXtdixhkPefcL2bLX5JK9F0LGiaaTVj0rMypU3iDDwQJbCUllQdY07N9vVZ6keZLqQDXAeq2TWiBmqm7_3TENp5zdVMuQTWTVfzYx9eDs8RfPsIaIYfWd1i8x3hSrUdKmKd3G3bkzJDRFHQgYPm208r9hXcxj5pbydyWM9xSutIlHTBXOyN1EGWRbfN_oDJRoYYbhAb3OrPu6tub7D27ctc68xmXPC3Fo0j8ROzmIoq8MOUXlI21ZMCDGjCAHvRLJzUY8pLPvbWPyAuNhaLa6eOEwkSvgfVJFQecQ07PGkR8F9CkriqesBShPNhQCTi3bP8clgcJ1fIfyjDcymz33qNFMnxDmX8Wmx4ml3p7FVw3vXTCMuaSrevNCHcoCbQF4fTJKVJ4IalkiHgbYSlm-luf2IEI_6TFUTTmM6Id2MFqVDDFXWCpAKk3_PfZtbsDP-Ov0hy39xsAnnZSvHvTY7v-ITvgMc-SMBOftrLnam9IDqCXgtfoqMoyP2Brn2qEVcsgUaCpkCv8FVFVp2rbZaiT1sFDUw1kWkNfmd0fXrEcyAJsDBVEuG7u3rHNWmDpBms8IHQnU3oJHS-VM_yhiNv0jc4jDF9iozU8YedV_j968IorYRIri_5lzPgbll2htOQrtlklaKX-9LNjhw0jTyeYssjro1NF45UPxQaf3nJ4laRID7ZwBFHNDeiCvJL8NtrxxqxGfu0c5nLeaM2a6aza5iKcW70UbIr9AvFFPs_SoXdSF3I2FH7OmukJNziPRA8wnlTs2U50CNIQwqVVkiM39KkZAs2AeU-cnL6Ls4EOyTdLly1XgdbkuHh4vzwgMAb3Wy7rhJ7XNW8wF_6rTn4b-30QlEg5PsB7PMpk0C3Y-t0FlJhpwwhOvUGzOsvn1px_u6dKVaaWwUq1czFrg_0RkaYjTGKaz4DAg-AtFzEk-TEwIgxxDvTo24EK6WDaoAACK693ktoLW0tr25FCWY53FhVkYNbuM3gk_8MhfAm4ZHVWsn22PkbUtyoA2DAPIEutK-XpntdpZq6-kGNjN6tyqLFrXHmjwvrPCcPjsM8CR2x47gmLCov10AOHSvjrNJJVlK3n7cpBBdDquJ2ze8CHnzplVZ82BnDI2thavwCc2Andov8arBgmxJ_22yGeexsex-rHsqtXAqLLQUudSURsLqr8Pyi8M2AQqT-_797WaHaxqPdndUehCFSkJIdYYz87H4cidhY5FAe-u5Sf_0_2_78JY9j2_zbx020enxtaj1SGWmOkgrctpN6NrkibJ4LuUsBWHUCQyawHlRuWpoM41W11aU8lrtWQnj7m_xisLtyQsL-MgyYPPVOCiPrAZ3siQz1hECH1RBScsque14-2LM5Bn-rGnCSvEyZ-JxeGSrNs70_hb34-tLKUST36TfLwOFiOKXUVGrA9uy4mwpKB4uOvyApmi4NRcu.PoEcLGQ-nEwuPX5Hg9rcPw"
)

while True:
    prompt = input("You: ")
    resp = cb.get_chat_response(prompt)
    print("Bot: ", resp["message"])
