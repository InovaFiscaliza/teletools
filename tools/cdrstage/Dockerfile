FROM postgres:18

# Install extensions available from official packages
RUN apt-get update && apt-get install -y \
    postgresql-18-postgis-3 \
    postgresql-18-pgrouting \
    postgresql-contrib-18 \
    postgresql-server-dev-18 \
    build-essential \
    zlib1g-dev \
    pkg-config \
    libgdal-dev \
    python3-gdal \
    git

# Clone the system_stats repository
RUN git clone https://github.com/EnterpriseDB/system_stats.git /tmp/system_stats

# Compile and install the extension
WORKDIR /tmp/system_stats
RUN make USE_PGXS=1
RUN make install USE_PGXS=1

# Clone the ogr_fdw source from GitHub
RUN git clone https://github.com/pramsey/pgsql-ogr-fdw.git /tmp/pgsql-ogr-fdw

# Build and install the extension
WORKDIR /tmp/pgsql-ogr-fdw
RUN make
RUN make install

# Clean up to reduce the final image size
RUN apt-get remove -y \
    build-essential \
    zlib1g-dev \
    pkg-config \
    libgdal-dev \
    git \
    make && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/system_stats /tmp/pgsql-ogr-fdw

# Change default working directory
WORKDIR /var/lib/postgresql