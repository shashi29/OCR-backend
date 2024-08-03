from langchain_unstructured import UnstructuredLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

loader = UnstructuredLoader("/home/vish.dharmapala.vega/OCR-backend/Payslip_2024-06-30.pdf", strategy="fast")

documents = loader.load()
chunk_size = 400
chunk_overlap = 0

# text splitting
text_splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size, chunk_overlap = chunk_overlap)
docs = text_splitter.split_documents(documents=documents)

print(docs)