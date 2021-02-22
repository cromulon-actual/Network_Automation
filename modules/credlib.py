class credential:
    def __init__(
        self,
        username=None,
        password=None,
        url=None,
        api=None,
        sheetid=None,
        sender_email=None,
        receiver_email=None,
    ):
        self.url = url
        self.username = username
        self.userpass = password
        self.api = api
        self.sheetid = sheetid
        self.sender_email = sender_email
        self.receiver_email = receiver_email