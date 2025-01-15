
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
    return False