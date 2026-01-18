# Model Tool Support Matrix

## Tool Support Verified (Local)

| Model                | Size | Tool Support | Notes                                     |
| :------------------- | :--- | :----------- | :---------------------------------------- |
| **qwen3:14b**        | 14GB | **YES**      | Works well with basic tools and skills.   |
| **codellama:13b**    | 13GB | NO           | Fails with 400 error when tools provided. |
| **deepseek-r1:14b**  | 14GB | NO           | Fails with 400 error when tools provided. |
| **phi4:14b**         | 14GB | ?            | Not yet verified.                         |
| **gemma3:12b**       | 12GB | ?            | Not yet verified.                         |
| **mistral-nemo:12b** | 12GB | ?            | Not yet verified.                         |

## Tool Support Verified (GCP Vertex AI)

| Model                | Version                | Tool Support | Notes                                      |
| :------------------- | :--------------------- | :----------- | :----------------------------------------- |
| **Gemini 2.5 Flash** | `gemini-2.5-flash`     | **YES**      | Verified connectivity and tool capability. |
| **Gemini 2.5 Pro**   | `gemini-2.5-pro`       | **YES**      | Suggested for complex reasoning.           |
| **Gemini 3 Pro**     | `gemini-3-pro-preview` | **YES**      | Cutting edge (Preview).                    |
