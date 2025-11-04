#!/bin/bash
export NEO4J_URI="neo4j+s://93be6d27.databases.neo4j.io:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_new_clone_password"

echo "Network check:"
nc -zv ${NEO4J_URI#*//} 7687 || echo "Port unreachable"

echo "Cypher Shell test:"
cypher-shell -a $NEO4J_URI -u $NEO4J_USER -p $NEO4J_PASSWORD --database neo4j -e "RETURN 'Bash test OK'" || echo "Cypher failed"

echo "Python test (in venv):"
source venv_nasa/bin/activate && python test_aura.py && deactivate
