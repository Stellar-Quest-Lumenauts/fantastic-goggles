import postbin


def upload_to_hastebin(content: str):
    """
    Upload a given content to hastebin.com
    Returns URL of uploaded content
    """
    return postbin.postSync(content)
