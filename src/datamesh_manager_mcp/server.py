from typing import Any, List, Dict, Optional
import logging
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from .datameshmanager.datamesh_manager_client import DataMeshManagerClient

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("datamesh-manager")

# Prompts
@mcp.prompt(name="Initial Prompt")
def initial_prompt() -> str:
    return """
You are now connected to the Data Mesh Manager through the Model Context Protocol (MCP).

Data Mesh Manager lists data products in the organization that you can use to get domain-specific data.

1. DISCOVERING DATA PRODUCTS
a) You can use the dataproduct_list tool to list data products in the organization. 
   You can add filters to the dataproduct_list tool to filter data products by name, description, owner, and status.
b) Alternatively, you can use the dataproduct_search tool to search for data products by semantics search, where more information are indexed.

2. GETTING DATA PRODUCT DETAILS
  - Both tools above return the data product ID.
  - You can use the dataproduct_get tool to get the details of a data product.
  - A data product contains a list of output ports. An output port can be associated with a data contract.
  - The output port includes server information to physically access the data (e.g., Databricks, Snowflake, etc.)

3. WORKING WITH DATA CONTRACTS
  - If an output port links to a data contract, you can use the datacontract_get tool to get the details of the data contract.
  - A data contract contains the terms of use for accessing the data. You must adhere to the terms of use when accessing the data.
  - A data contract contains the schema of the data model. Use this schema to identify if the data product is suitable for your use case.
  - Use the schema if you later build queries (e.g., SQL) to access the data.
  - The data model also contains descriptions and other information about the data that you can use to understand the data."""


@mcp.tool()
async def dataproduct_list(
    search_term: Optional[str] = None,
    archetype: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lists all available Data Products.
    
    Args:
        search_term: Search term to filter data products. Searches in the id, title, and description. 
                    Multiple search terms are supported, separated by space.
        archetype: Filter for specific data product types. Typical values are: consumer-aligned, 
                  aggregate, source-aligned, application, dataconsumer
        status: Filter for specific status, such as active
    """
    logger.info(f"dataproduct_list called with search_term={search_term}, archetype={archetype}, status={status}")
    
    try:
        client = DataMeshManagerClient()
        data_products = await client.get_data_products(
            query=search_term,
            archetype=archetype,
            status=status
        )
        
        if not data_products:
            logger.info("dataproduct_list returned empty list")
            return []
        
        # Return structured list of data products
        formatted_products = []
        for dp in data_products:
            formatted_product = {
                "id": dp.get("id", "N/A"),
                "name": dp.get("title") or dp.get("info", {}).get("title") or "N/A",
                "description": dp.get("description") or dp.get("info", {}).get("description") or "N/A",
                "owner": dp.get("owner") or dp.get("info", {}).get("owner") or "N/A"
            }
            formatted_products.append(formatted_product)
        
        logger.info(f"dataproduct_list returned {len(formatted_products)} data products")
        return formatted_products
        
    except ValueError as e:
        logger.error(f"dataproduct_list ValueError: {str(e)}")
        return [{"error": str(e)}]
    except Exception as e:
        logger.error(f"dataproduct_list Exception: {str(e)}")
        return [{"error": f"Error fetching data products: {str(e)}"}]


@mcp.tool()
async def dataproduct_search(search_term: str) -> List[Dict[str, Any]]:
    """
    A semantic search for data products for a specific user question or use case.
    
    Args:
        search_term: Search term to filter data products. Searches in the id, title, and description. Use simple search terms.            
    """
    logger.info(f"dataproduct_search called with search_term={search_term}")
    
    try:
        client = DataMeshManagerClient()
        search_results = await client.search(search_term, resource_type="DATA_PRODUCT")
        data_products = search_results.get("results", [])
        
        if not data_products:
            logger.info("dataproduct_search returned empty list")
            return []
        
        # Return structured list of data products
        formatted_products = []
        for dp in data_products:
            formatted_product = {
                "id": dp.get("id", "N/A"),
                "name": dp.get("name") or "N/A",
                "description": dp.get("description") or dp.get("info", {}).get("description") or "N/A",
                "ownerId": dp.get("ownerId") or "N/A",
                "ownerName": dp.get("ownerName") or "N/A",
            }
            formatted_products.append(formatted_product)
        
        logger.info(f"dataproduct_search returned {len(formatted_products)} data products")
        return formatted_products
        
    except ValueError as e:
        logger.error(f"dataproduct_search ValueError: {str(e)}")
        return [{"error": str(e)}]
    except Exception as e:
        logger.error(f"dataproduct_search Exception: {str(e)}")
        return [{"error": f"Error searching data products: {str(e)}"}]


@mcp.tool()
async def dataproduct_get(data_product_id: str) -> str:
    """
    Get a data product by its ID. The data product contains all its output ports and server information.
    The response may include a data contract ID.
    You can use the datacontract_get tool to get the details of the data contract for more semantic information and terms of use..
    
    Args:
        data_product_id: The data product ID.
    """
    logger.info(f"dataproduct_get called with data_product_id={data_product_id}")
    
    try:
        client = DataMeshManagerClient()
        data_product = await client.get_data_product(data_product_id)
        
        if not data_product:
            logger.info(f"dataproduct_get: data product {data_product_id} not found")
            return "Data product not found"
        
        # Convert the data product to YAML format
        import yaml
        yaml_data = yaml.dump(data_product, default_flow_style=False, sort_keys=False)
        logger.info(f"dataproduct_get successfully retrieved data product {data_product_id}")
        return yaml_data
        
    except ValueError as e:
        logger.error(f"dataproduct_get ValueError: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"dataproduct_get Exception: {str(e)}")
        return f"Error fetching data product: {str(e)}"


@mcp.tool()
async def datacontract_get(data_contract_id: str) -> str:
    """
    Get a data contract by its ID.
    
    Args:
        data_contract_id: The data contract ID.
    """
    logger.info(f"datacontract_get called with data_contract_id={data_contract_id}")
    
    try:
        client = DataMeshManagerClient()
        data_contract = await client.get_data_contract(data_contract_id)
        
        if not data_contract:
            logger.info(f"datacontract_get: data contract {data_contract_id} not found")
            return "Data contract not found"
        
        # Convert the data contract to YAML format
        import yaml
        yaml_data = yaml.dump(data_contract, default_flow_style=False, sort_keys=False)
        logger.info(f"datacontract_get successfully retrieved data contract {data_contract_id}")
        return yaml_data
        
    except ValueError as e:
        logger.error(f"datacontract_get ValueError: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"datacontract_get Exception: {str(e)}")
        return f"Error fetching data contract: {str(e)}"


if __name__ == "__main__":
    # Set up logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting DataMesh Manager MCP server")
    
    # Initialize and run the server
    mcp.run(transport='stdio')