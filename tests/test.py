import pytest, sys, os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)

from threadspipepy.threadspipe import ThreadsPipe


def test_user_id_nd_access_token_type_error():
    """
        test_user_id_nd_access_token_type_error
        Tests for the user_id and access_token parameters are required upon initialization
    """
    with pytest.raises(TypeError):
        th_init = ThreadsPipe()

def test_passed_parameters_were_set():
    """
        test_passed_parameters_were_set
        Tests that the passed parameters on initialization were set
    """
    th_init = ThreadsPipe(
        user_id="test_user_id",
        access_token="test_access_token",
        gh_username="test_gh_username"
    )

    assert th_init.__threads_user_id__ == "test_user_id"
    assert th_init.__threads_access_token__ == "test_access_token"
    assert th_init.__gh_username__ == "test_gh_username"

def test_update_param_method():
    """
        test_update_param_method
        Tests that the update_param method updates the passed parameters
    """
    th_init = ThreadsPipe(
        user_id="test_user_id",
        access_token="test_access_token",
    )
    th_init.update_param(
        user_id="updated_user_id",
        access_token="updated_access_token",
    )

    assert th_init.__threads_user_id__ == "updated_user_id"
    assert th_init.__threads_access_token__ == "updated_access_token"

def test_post_splitting_test():
    """
        test_post_splitting_test
        tests the post splitting into batches if the method is working corectly
    """
    th_init = ThreadsPipe(
        user_id="test_user_id",
        access_token="test_access_token",
    )
    post_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc ultrices, ante in feugiat pharetra, lectus nunc tincidunt nibh, in efficitur sapien massa nec dolor. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Sed euismod, nisi vel semper ultricies, augue velit blandit odio, et ultrices ante quam id orci. Donec euismod, erat non tincidunt aliquet, velit dui ultrices lorem, quis malesuada sapien diam a nunc. Sed et velit vitae arcu luctus ornare. \
        \
        Maecenas placerat, quam id aliquet volutpat, odio nisi lacinia nisl, quis scelerisque enim felis non ipsum. Duis et nulla sit amet elit aliquam aliquet. Nulla facilisi. Sed a lacus et quam elementum pulvinar. Sed sed sapien et nunc tempus lacinia. Nulla facilisi. Nulla facilisi. Mauris viverra lacinia mauris, quis blandit enim ultricies vel. \
            \
        Nulla facilisi. Suspendisse venenatis, urna sit amet rhoncus dignissim, nisl nunc pharetra est, sit amet auctor eros nunc id mi. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Donec pellentesque, tellus et feugiat porttitor, sapien ante sollicitudin sapien, vitae aliquet erat mauris quis ipsum.\
            \
        Nulla facilisi. Maecenas id massa sed odio vulputate dignissim. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Mauris non ipsum sed ante elementum aliquet. Maecenas id massa sed odio vulputate dignissim. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Sed et velit vitae arcu luctus ornare.\
            \
        Nulla facilisi. Sed et velit vitae arcu luctus ornare. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et velit vitae arcu luctus ornare. Nulla facilisi. Sed et vel"
    
    splitted_post = th_init.__split_post__(
        post=post_text,
        tags=["#tag1", "#tag2", "#tag3", "#tag3"]
    )
    # the returned item type must be list
    assert type(splitted_post) == list
    # check the length of the returned list is greater than zero
    assert len(splitted_post) > 0
    # check if the length of the first batch is 500
    assert len(splitted_post[0]) == 500

def test___is_base64___method():
    """
        test___is_base64___method
        Check if the is base64 is working correctly
    """
    th_init = ThreadsPipe(
        user_id="test_user_id",
        access_token="test_access_token",
    )
    b64_img = "R0lGODlhPQBEAPeoAJosM//AwO/AwHVYZ/z595kzAP/s7P+goOXMv8+fhw/v739/f+8PD98fH/8mJl+fn/9ZWb8/PzWlwv///6wWGbImAPgTEMImIN9gUFCEm/gDALULDN8PAD6atYdCTX9gUNKlj8wZAKUsAOzZz+UMAOsJAP/Z2ccMDA8PD/95eX5NWvsJCOVNQPtfX/8zM8+QePLl38MGBr8JCP+zs9myn/8GBqwpAP/GxgwJCPny78lzYLgjAJ8vAP9fX/+MjMUcAN8zM/9wcM8ZGcATEL+QePdZWf/29uc/P9cmJu9MTDImIN+/r7+/vz8/P8VNQGNugV8AAF9fX8swMNgTAFlDOICAgPNSUnNWSMQ5MBAQEJE3QPIGAM9AQMqGcG9vb6MhJsEdGM8vLx8fH98AANIWAMuQeL8fABkTEPPQ0OM5OSYdGFl5jo+Pj/+pqcsTE78wMFNGQLYmID4dGPvd3UBAQJmTkP+8vH9QUK+vr8ZWSHpzcJMmILdwcLOGcHRQUHxwcK9PT9DQ0O/v70w5MLypoG8wKOuwsP/g4P/Q0IcwKEswKMl8aJ9fX2xjdOtGRs/Pz+Dg4GImIP8gIH0sKEAwKKmTiKZ8aB/f39Wsl+LFt8dgUE9PT5x5aHBwcP+AgP+WltdgYMyZfyywz78AAAAAAAD///8AAP9mZv///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAKgALAAAAAA9AEQAAAj/AFEJHEiwoMGDCBMqXMiwocAbBww4nEhxoYkUpzJGrMixogkfGUNqlNixJEIDB0SqHGmyJSojM1bKZOmyop0gM3Oe2liTISKMOoPy7GnwY9CjIYcSRYm0aVKSLmE6nfq05QycVLPuhDrxBlCtYJUqNAq2bNWEBj6ZXRuyxZyDRtqwnXvkhACDV+euTeJm1Ki7A73qNWtFiF+/gA95Gly2CJLDhwEHMOUAAuOpLYDEgBxZ4GRTlC1fDnpkM+fOqD6DDj1aZpITp0dtGCDhr+fVuCu3zlg49ijaokTZTo27uG7Gjn2P+hI8+PDPERoUB318bWbfAJ5sUNFcuGRTYUqV/3ogfXp1rWlMc6awJjiAAd2fm4ogXjz56aypOoIde4OE5u/F9x199dlXnnGiHZWEYbGpsAEA3QXYnHwEFliKAgswgJ8LPeiUXGwedCAKABACCN+EA1pYIIYaFlcDhytd51sGAJbo3onOpajiihlO92KHGaUXGwWjUBChjSPiWJuOO/LYIm4v1tXfE6J4gCSJEZ7YgRYUNrkji9P55sF/ogxw5ZkSqIDaZBV6aSGYq/lGZplndkckZ98xoICbTcIJGQAZcNmdmUc210hs35nCyJ58fgmIKX5RQGOZowxaZwYA+JaoKQwswGijBV4C6SiTUmpphMspJx9unX4KaimjDv9aaXOEBteBqmuuxgEHoLX6Kqx+yXqqBANsgCtit4FWQAEkrNbpq7HSOmtwag5w57GrmlJBASEU18ADjUYb3ADTinIttsgSB1oJFfA63bduimuqKB1keqwUhoCSK374wbujvOSu4QG6UvxBRydcpKsav++Ca6G8A6Pr1x2kVMyHwsVxUALDq/krnrhPSOzXG1lUTIoffqGR7Goi2MAxbv6O2kEG56I7CSlRsEFKFVyovDJoIRTg7sugNRDGqCJzJgcKE0ywc0ELm6KBCCJo8DIPFeCWNGcyqNFE06ToAfV0HBRgxsvLThHn1oddQMrXj5DyAQgjEHSAJMWZwS3HPxT/QMbabI/iBCliMLEJKX2EEkomBAUCxRi42VDADxyTYDVogV+wSChqmKxEKCDAYFDFj4OmwbY7bDGdBhtrnTQYOigeChUmc1K3QTnAUfEgGFgAWt88hKA6aCRIXhxnQ1yg3BCayK44EWdkUQcBByEQChFXfCB776aQsG0BIlQgQgE8qO26X1h8cEUep8ngRBnOy74E9QgRgEAC8SvOfQkh7FDBDmS43PmGoIiKUUEGkMEC/PJHgxw0xH74yx/3XnaYRJgMB8obxQW6kL9QYEJ0FIFgByfIL7/IQAlvQwEpnAC7DtLNJCKUoO/w45c44GwCXiAFB/OXAATQryUxdN4LfFiwgjCNYg+kYMIEFkCKDs6PKAIJouyGWMS1FSKJOMRB/BoIxYJIUXFUxNwoIkEKPAgCBZSQHQ1A2EWDfDEUVLyADj5AChSIQW6gu10bE/JG2VnCZGfo4R4d0sdQoBAHhPjhIB94v/wRoRKQWGRHgrhGSQJxCS+0pCZbEhAAOw=="
    is_b64 = th_init.__is_base64__(b64_img)
    random_text = "hdbchdschsabchbcldschdbcdhcbsydgcdycbdlcbascba"
    is_rand_text_b64 = th_init.__is_base64__(random_text)

    # should return true for the base64 image
    assert is_b64 is True
    # the random text should return false
    assert is_rand_text_b64 is False

def test__is_url__method():
    """
        test__is_url__method
        This function tests for supported remote file urls
        Format is [url, expected check]
    """
    urls = [
        # long full urls
        ["https://thespacedevs-prod.nyc3.digitaloceanspaces.com/media/images/jamila_gilbert_image_20230508161019.png", True],
        ["https://www.digitaloceanspaces.com/media/images/jamila_gilbert_image_20230508161019.png",  True],
        ["https://images.unsplash.com/photo-1721332149371-fa99da451baa?q=80&w=2536&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDF8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", True],
        ["https://images.unsplash.com/?q=80&w=2536&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDF8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", True],
        ["https://images.unsplash.com?q=80&w=2536&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDF8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", True],

        # unsupported urls
        ["/path/to/file.jpg", False],
        ["C:/path/to/file.jpg", False],
        ["E:/Users/paulos_ab/path/to/file.jpg", False],
        ["https://example", False],
        ["https://localhost", False],

        # urls with ports are supported
        ["https://www.example.com:829/path/to/file.jpg?h=file&type=byte", True],
        ["https://example.com:9201/path/to/file.png", True],

        # urls with no schemes are supported and should be true
        ["example.com/path/to/file.jpg", True],
        ["example.com", True],

        # normal urls are also supported, though might be rejected
        ["https://google.com", True],

        # IP address urls and ones with port are supported
        ["192.0.0.0?h=file&type=byte", True],
        ["192.0.0.0/path/to/file.jpg?h=file&type=byte", True],
        ["192.0.0.0:80/path/to/file.jpg?h=file&type=byte", True],
        ["142.250.184.174/path/to/file.jpg?h=file&type=byte", True],
        ["https://142.250.184.174:80/path/to/file.jpg?h=file&type=byte", True],
        ["http://142.250.184.174:80/path/to/file.jpg?h=file&type=byte", True],
    ]

    th_init = ThreadsPipe(
        user_id="test_user_id",
        access_token="test_access_token",
    )

    for url in urls:
        print('url', url[0], th_init.__file_url_reg__.fullmatch(url[0]))
        assert (th_init.__file_url_reg__.fullmatch(url[0]) is not None) == url[1]

