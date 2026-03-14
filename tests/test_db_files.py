from database.db_files_data import (
    upsert_file_data,
    get_file_data,
    search_files_by_tag,
    delete_file_data
)
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone

def run_tests():
    print("--- Starting DB Tests ---")

    # 1. Test Upsert (Main File)
    print("\n1. Testing Upsert (Main File)...")
    now = datetime.now(timezone.utc)
    main_id = upsert_file_data(
        file_path="dummy_folder/test_document.txt",
        section_name="", # Empty string means it's the main file
        parent_id=None,
        file_last_modified=now,
        short_summary="This is a test document.",
        long_summary="This is a much longer summary of the test document just to see if the database handles it correctly.",
        tags=["test", "python", "database"]
    )
    print(f"Main file inserted with ID: {main_id}")

    # 2. Test Upsert (Section/Chapter)
    print("\n2. Testing Upsert (Section)...")
    section_id = upsert_file_data(
        file_path="dummy_folder/test_document.txt",
        section_name="Chapter 1",
        parent_id=main_id, # Linking this section to the main file we just created
        file_last_modified=now,
        short_summary="Summary of Chapter 1.",
        long_summary="Longer summary of Chapter 1 detailing all the internal test operations.",
        tags=["chapter", "test"]
    )
    print(f"Section inserted with ID: {section_id}")

    # 3. Test Retrieve Data
    print("\n3. Testing Get File Data...")
    main_file_data = get_file_data(file_path="dummy_folder/test_document.txt", section_name="")
    if main_file_data:
        print(f"Retrieved Main File Summary: '{main_file_data['short_summary']}'")
    else:
        print("Failed to retrieve Main File.")

    section_data = get_file_data(file_path="dummy_folder/test_document.txt", section_name="Chapter 1")
    if section_data:
        print(f"Retrieved Section Summary: '{section_data['short_summary']}'")
    else:
        print("Failed to retrieve Section.")

    # 4. Test Search by Tag
    print("\n4. Testing Search by Tag ('python')...")
    search_results = search_files_by_tag("python")
    print(f"Found {len(search_results)} result(s):")
    for res in search_results:
        print(f" - Path: {res['file_path']} | Section: '{res['section_name']}'")

    # 5. Test Delete (and verify Cascade behavior)
    print("\n5. Testing Delete (Cascade)...")
    delete_success = delete_file_data(file_path="dummy_folder/test_document.txt")
    print(f"Delete operation successful: {delete_success}")

    # Verify that the section was also deleted automatically
    check_deleted = get_file_data(file_path="dummy_folder/test_document.txt", section_name="Chapter 1")
    if not check_deleted:
        print("Verified: Section was successfully deleted automatically (ON DELETE CASCADE works!).")
    else:
        print("Uh oh, section still exists in the database.")

    print("\n--- Tests Completed ---")

if __name__ == "__main__":
    run_tests()