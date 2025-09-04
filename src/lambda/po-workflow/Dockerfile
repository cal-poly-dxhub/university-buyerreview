FROM public.ecr.aws/lambda/python:3.12

# Copy requirements first for better caching
COPY requirements.txt .

# Install font stack (AL2023 base). Use microdnf or dnf depending on image.
RUN microdnf install -y fontconfig dejavu-sans-fonts dejavu-serif-fonts freetype harfbuzz pango cairo && microdnf clean all || \
    (dnf -y install fontconfig dejavu-sans-fonts dejavu-serif-fonts freetype harfbuzz pango cairo && dnf clean all)

ENV XDG_CACHE_HOME=/tmp
ENV HOME=/tmp
RUN mkdir -p /var/cache && ln -sfn /tmp/fontconfig /var/cache/fontconfig
COPY fontconfig/local.conf /etc/fonts/local.conf

# Install Python dependencies
RUN dnf install -y pango && dnf clean all
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire workspace
COPY . .

COPY Agents/* ${LAMBDA_TASK_ROOT}
COPY Data/* ${LAMBDA_TASK_ROOT}
COPY Graphs/* ${LAMBDA_TASK_ROOT}
COPY pages/* ${LAMBDA_TASK_ROOT}
COPY Parser_Prompts/* ${LAMBDA_TASK_ROOT}
COPY Task_Prompts/* ${LAMBDA_TASK_ROOT}
COPY Tools_Config/* ${LAMBDA_TASK_ROOT}
COPY utils/* ${LAMBDA_TASK_ROOT}
COPY main.py ${LAMBDA_TASK_ROOT}
COPY model_registry.py ${LAMBDA_TASK_ROOT}
COPY prompt_loader.py ${LAMBDA_TASK_ROOT}
COPY state.py ${LAMBDA_TASK_ROOT}
COPY tools.py ${LAMBDA_TASK_ROOT}

# Set environment variables for Lambda
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}"
ENV LAMBDA_TASK_ROOT="${LAMBDA_TASK_ROOT}"

# Make sure the handler function is accessible
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}:${PYTHONPATH}"

# Set the Lambda handler
CMD ["main.handler"]
