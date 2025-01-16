from django.conf import settings
import requests
from xml.etree.ElementTree import Element, SubElement, tostring

def create_order(order, adress_data):
    """
    Creates an order and places it with GBF.
    """
    order_number = _generate_order_number(order)

    # generate XML
    order_xml = _generate_order_xml(order, adress_data, order_number)

    # make order with GBF
    _place_order_with_GBF(order_xml)
    
    return order_number

def _generate_order_number(order):
    """
    Generates an order number based on the primary key of the order object.
    """
    return "EDROP-%05d"%(order.pk)

def _generate_order_xml(order, address_data, order_number):
    # TODO: generate order xml according to GBF documentation
    xml = f"""
        <Orders>
            <Order>
                <OrderNumber>{order_number}</OrderNumber>
                <ClientAccount>{order.}</ClientAccount>
                <OrderDate>{order.date}</OrderDate>
                <ShippingInfo>
                    <Address>
                        <Company>{address_data}</Company>
                        <Attention>{address_data}</Attention>
                        <AddressLine1>{address_data['street']}</AddressLine1>
                        <AddressLine2/>
                        <City>{address_data['city']}</City>
                        <State>{address_data['state']}</State>
                        <ZipCode>{address_data['zip']}</ZipCode>
                        <Country>{address_data['country']}</Country>
                        <PhoneNumber>{address_data}</PhoneNumber>
                        <FaxNumber>{address_data}</FaxNumber>
                    </Address>
                    <ShipMethod>FedEx 2Day AM</ShipMethod>
                </ShippingInfo>
                <LineItem>
                    <ItemNumber>FM-00049</ItemNumber>
                    <ItemQuantity>5</ItemQuantity>
                </LineItem>
            </Order>
        </Orders
    """
    orders = Element("Orders")
    order = SubElement(orders, "Order")

    order_num = SubElement(order, "OrderNumber")
    order_num.text = order_number

    client_account = SubElement(order, "ClientAccount")
    client_account.text = ""

    order_date = SubElement(order, "OrderDate")
    order_date.text = ""

    shipping_info = SubElement(order, "ShippingInfo")
    address = SubElement(shipping_info, "Address")
    ship_method = SubElement(shipping_info, "ShipMethod")
    ship_method.text = ""

    line_item = SubElement(shipping_info, "LineItem")
    
    company = SubElement(address, "Company")
    company.text = ""

    attention = SubElement(address, "Attention")
    attention.text = ""

    address_1 = SubElement(address, "AddressLine1")
    address_1 = address_data["street"]
    address_2 = SubElement(address, "AddressLine2")
    city = SubElement(address, "City")
    city.text = address_data["city"]
    state = SubElement(address, "State")
    state.text = address_data["state"]
    zip_code = SubElement(address, "ZipCode")
    zip_code.text = address_data["zip"]
    country = SubElement(address, "Country")
    country.text = address_data["country"]
    phone = SubElement(address, "PhoneNumber")
    phone.text = address_data[""]
    fax = SubElement(address, "FaxNumber")
    fax.text = address_data[""]

    item_number = SubElement(line_item, "ItemNumber")
    item_number.text = ""

    item_quantity = SubElement(line_item, "ItemQuantity")
    item_quantity.text = ""

    #return (tostring(orders))
    return "xml"


def _place_order_with_GBF(order_xml):
    """
    Makes a POST request to the GBF endpoint /oap/api/order with the proper
    order XML. 

    Returns:
    - True if GBF returns true
    - False if GBF returns false
    """
    # make post request to GBF
    # By default requests should be made as "test" via an environment variable.
    # Once we go live, the environemnt variable needs to be set to true explictly,
    headers = {f"'Authorization': 'Bearer {settings.GBF_TOKEN}'"}
    content = {orderXml: order_xml, test: settings.GBF_TEST_FLAG}
    response = requests.post(f"{settings.GBF_URL}order", data=content, headers=headers)
    
    if response == 'true':
        return True
    return False