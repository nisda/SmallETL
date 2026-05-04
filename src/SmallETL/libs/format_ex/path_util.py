from typing import List, Type
import re
from decimal import Decimal

def get_nested_data(data, path):

    # a[0][b] -> ['a', '0', 'b'] に分解
    # a.0.b -> ['a', '0', 'b'] に分解
    parts:List[str] = re.findall(r'[^\[\]\.]+', path)
    
    process_nodes = []
    node = data
    for p in parts:
        try:
            if isinstance(node, (list, tuple)):
                node = node[int(p)]
            elif isinstance(node, dict):
                
                if p.isnumeric():
                    if int(p) in node.keys():
                        node = node[int(p)]
                        continue
                    if float(p) in node.keys():
                        node = node[float(p)]
                        continue
                    if Decimal(p) in node.keys():
                        node = node[Decimal(p)]
                        continue
                node = node[p]
            else:
                raise TypeError(f"Node specification is not supported.")
            
        except Exception as e:
            e_type:Type = type(e)
            e_msg:str   = f"{str(e).rstrip('.')}. occurred at path='.{'.'.join(process_nodes)}'<{type(node).__name__}>"
            raise e_type(e_msg) from e

        process_nodes.append(p)
    return node
