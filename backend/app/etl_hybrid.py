# Around line 175-200, replace the table storage section:

        # 6) Store table metadata
        preview = df.head(5).to_dict(orient="records")
        
        meta.update({
            "doc_id": doc_id,
            "user_id": user_id,
            "project_id": project_id,
            "description": description,
            "table_type": table_type,
            "data_type": "tabular",
            "artifact_type": artifact_type,
            "preview": preview,  # Add here instead
            "row_count": len(df),
            "column_count": df.shape[1],
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "updated_at": datetime.datetime.now(datetime.timezone.utc),
        })
        
        try:
            upsert_table(
                doc_id=doc_id,
                table_id=table_id,
                meta=meta,
                column_count=df.shape[1],
                properties=meta
            )
            tables_written += 1
            
            table_metadata_list.append({
                "table_id": table_id,
                "table_type": table_type,
                "page": page,
                "rows": len(df),
                "columns": len(columns)
            })
            
        except Exception as e:
            import traceback
            print(f"[ETL:HYBRID] - Failed to upsert table {table_id}: {e}")
            traceback.print_exc()
            continue