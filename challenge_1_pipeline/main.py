from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pipeline import process_pipeline
from outputs import init_db, init_redis, batch_write_db, batch_write_queue


app = FastAPI()
init_db()


class WebhookPayload(BaseModel):
    data: list

    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {"data": {"user_id": 456, "action": "view"}},
                    {"data": {"user_id": 789, "action": "purchase", "amount": 99.99}}
                ]
            }
        }


@app.post("/webhook")
async def webhook(payload: WebhookPayload):
    """
    Webhook endpoint that receives JSON data stream and writes both into DB and redis queue
    """
    try:

        # Process data through the pipeline
        processed = process_pipeline(iter(payload.data))

        # Convert generator to list for dual writes (tee could be used for larger streams)
        processed_list = list(processed)

        # Write to database
        db_count = batch_write_db(iter(processed_list))

        # Write to Redis queue
        try:
            redis_client = init_redis()
            redis_client.ping()
        except Exception as redis_error:
            print(f"Redis connection failed: {redis_error}")
            raise

        queue_count = batch_write_queue(iter(processed_list), redis_client=redis_client)

        return {
            "status": "success",
            "records_received": len(payload.data),
            "records_written_db": db_count,
            "records_written_queue": queue_count
        }

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)