<!-- gemma4:31b-cloud -->
<!-- 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 -->
<!-- The issue is with the path need to extract the accurate path -->
<!-- D:\\AI-Restart-2026\\Complete GEN AI Journey - Notes\\DataIngestion_Pipeline\\config\\data\\uploads\\fe0de0706ed24d9387bdce7f5e50bb59_NIPS-2017-attention-is-all-you-need-Paper.p - Wrong one -->
<!-- D:/AI-Restart-2026/Complete GEN AI Journey - Notes/DataIngestion_Pipeline/config/data/processed/Attention.pdf correct one -->
<!-- python -m src.retrievers.initiate_embeddings_and_retrieval -->

<!--  -->
<!-- 
left with the retriever mechanism for new vector db 
polish each and every import and initilization object
try to use the old classes to do it 
next build the api endpoint to test it 
complete the testing and implement the complete frontend to test it from bottom -->
uvicorn src.api.main:app --reload