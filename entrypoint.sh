

#!/bin/bash
echo "Starting Streamlit app on port $PORT"
exec streamlit run streamlit_main_app.py --server.port=${PORT:-8080} --server.enableCORS=false --server.enableXsrfProtection=false


