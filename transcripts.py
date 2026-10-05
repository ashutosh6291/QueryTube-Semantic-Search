from supadata import Supadata, SupadataError
import csv
import time
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def extract_text_from_transcript_data(transcript_data):
    """
    Extract and concatenate text from TranscriptChunk objects, filtering for English only
    """
    text_parts = []
    
    if hasattr(transcript_data, 'content') and isinstance(transcript_data.content, list):
        # If it has a content attribute with list of chunks
        for chunk in transcript_data.content:
            if hasattr(chunk, 'text') and hasattr(chunk, 'lang') and chunk.lang == 'en':
                text_parts.append(chunk.text)
            elif hasattr(chunk, 'text') and not hasattr(chunk, 'lang'):
                # If no language specified, assume English
                text_parts.append(chunk.text)
    elif hasattr(transcript_data, 'text'):
        # If it's a simple text response
        text_parts.append(transcript_data.text)
    elif isinstance(transcript_data, dict):
        # If it's a dictionary
        if 'content' in transcript_data and isinstance(transcript_data['content'], list):
            for chunk in transcript_data['content']:
                if isinstance(chunk, dict) and 'text' in chunk:
                    # Check if language is specified and is English
                    if chunk.get('lang') == 'en' or 'lang' not in chunk:
                        text_parts.append(chunk['text'])
        elif 'text' in transcript_data:
            text_parts.append(transcript_data['text'])
    elif isinstance(transcript_data, list):
        # If it's directly a list of chunks
        for chunk in transcript_data:
            if hasattr(chunk, 'text') and hasattr(chunk, 'lang') and chunk.lang == 'en':
                text_parts.append(chunk.text)
            elif hasattr(chunk, 'text') and not hasattr(chunk, 'lang'):
                text_parts.append(chunk.text)
            elif isinstance(chunk, dict) and 'text' in chunk:
                if chunk.get('lang') == 'en' or 'lang' not in chunk:
                    text_parts.append(chunk['text'])
    
    # Join all text parts with spaces
    full_text = ' '.join(text_parts)
    return full_text

def clean_transcript(raw_transcript):
    """
    Clean the transcript text by removing unwanted artifacts
    """
    if not raw_transcript:
        return ""
    
    text = str(raw_transcript)
    
    # Remove standalone [Music] tags but keep the text content
    text = re.sub(r'\s*\[Music\]\s*', ' ', text)
    text = re.sub(r'\s*\[Applause\]\s*', ' ', text)
    text = re.sub(r'\s*\[Laughter\]\s*', ' ', text)
    
    # Remove other common audio tags
    text = re.sub(r'\s*\[\s*\w+\s*\]\s*', ' ', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def extract_transcripts_to_csv(video_ids, api_key, csv_filename="video_transcripts.csv", delay=0.5):
    """
    Extract and clean English transcripts for multiple videos and save to CSV file
    """
    # Initialize Supadata client with API key
    client = Supadata(api_key=api_key)
    
    # Open CSV file for writing
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['video_id', 'raw_transcript', 'cleaned_transcript', 'status', 'word_count', 'language_notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Process each video
        for i, video_id in enumerate(video_ids):
            try:
                print(f"Processing {i+1}/{len(video_ids)}: {video_id}")
                
                # Convert video ID to full YouTube URL
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                
                # Use the transcript method with full YouTube URL
                transcript_data = client.transcript(youtube_url)
                
                # Extract English text from the structured data
                raw_transcript = extract_text_from_transcript_data(transcript_data)
                
                # Check if we got any English content
                language_notes = "English content found"
                if not raw_transcript.strip():
                    language_notes = "No English content found in transcript"
                    print(f"Warning: No English content for {video_id}")
                
                # Clean the transcript
                cleaned_transcript = clean_transcript(raw_transcript)
                word_count = len(cleaned_transcript.split())
                
                # Write successful result to CSV
                writer.writerow({
                    'video_id': video_id,
                    'raw_transcript': raw_transcript,
                    'cleaned_transcript': cleaned_transcript,
                    'status': 'success',
                    'word_count': word_count,
                    'language_notes': language_notes
                })
                
                print(f"Success: {video_id} ({word_count} English words)")
                
            except SupadataError as e:
                writer.writerow({
                    'video_id': video_id,
                    'raw_transcript': f"SupadataError: {str(e)}",
                    'cleaned_transcript': "",
                    'status': 'failed',
                    'word_count': 0,
                    'language_notes': "Error during extraction"
                })
                print(f"Failed: {video_id} - {str(e)}")
                
            except Exception as e:
                writer.writerow({
                    'video_id': video_id,
                    'raw_transcript': f"Unexpected error: {str(e)}",
                    'cleaned_transcript': "",
                    'status': 'failed',
                    'word_count': 0,
                    'language_notes': "Error during extraction"
                })
                print(f"Unexpected error for {video_id}: {str(e)}")
            
            # Add delay between requests
            if i < len(video_ids) - 1:
                time.sleep(delay)

def preview_transcript_structure(video_ids, api_key, sample_size=3):
    """
    Preview the structure of raw transcripts to understand language distribution
    """
    client = Supadata(api_key=api_key)
    
    print("Previewing transcript structure and language for first few videos:")
    print("=" * 60)
    
    for i, video_id in enumerate(video_ids[:sample_size]):
        try:
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            transcript_data = client.transcript(youtube_url)
            
            # Analyze language distribution in chunks
            if hasattr(transcript_data, 'content') and isinstance(transcript_data.content, list):
                languages = {}
                for chunk in transcript_data.content:
                    if hasattr(chunk, 'lang'):
                        lang = chunk.lang
                        languages[lang] = languages.get(lang, 0) + 1
                
                print(f"\nVideo {i+1}: {video_id}")
                print(f"Language distribution: {languages}")
            
            # Extract English text from structured data
            raw_transcript = extract_text_from_transcript_data(transcript_data)
            
            print("English transcript (first 500 chars):")
            print("-" * 40)
            print(raw_transcript[:500] + "..." if len(raw_transcript) > 500 else raw_transcript)
            print("-" * 40)
            
            # Show cleaned version
            cleaned = clean_transcript(raw_transcript)
            print("Cleaned English transcript (first 500 chars):")
            print("-" * 40)
            print(cleaned[:500] + "..." if len(cleaned) > 500 else cleaned)
            print("-" * 40)
            print(f"Word count: {len(cleaned.split())}")
            print("=" * 60)
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error previewing {video_id}: {str(e)}")
            print("=" * 60)

# Alternative: Force English language if supported by API
def extract_english_transcripts_with_language_param(video_ids, api_key, csv_filename="english_transcripts.csv", delay=0.5):
    """
    Alternative method that tries to force English language if the API supports it
    """
    client = Supadata(api_key=api_key)
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['video_id', 'transcript', 'status', 'word_count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, video_id in enumerate(video_ids):
            try:
                print(f"Processing {i+1}/{len(video_ids)}: {video_id}")
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                
                # Try to get English transcript specifically
                # Note: This depends on whether the Supadata API supports language parameter
                try:
                    # If the API supports language parameter
                    transcript_data = client.transcript(youtube_url, language='en')
                except:
                    # Fallback to default
                    transcript_data = client.transcript(youtube_url)
                
                raw_transcript = extract_text_from_transcript_data(transcript_data)
                cleaned_transcript = clean_transcript(raw_transcript)
                word_count = len(cleaned_transcript.split())
                
                writer.writerow({
                    'video_id': video_id,
                    'transcript': cleaned_transcript,
                    'status': 'success',
                    'word_count': word_count
                })
                
                print(f"Success: {video_id} ({word_count} words)")
                
            except Exception as e:
                writer.writerow({
                    'video_id': video_id,
                    'transcript': f"Error: {str(e)}",
                    'status': 'failed',
                    'word_count': 0
                })
                print(f"Failed: {video_id} - {str(e)}")
            
            if i < len(video_ids) - 1:
                time.sleep(delay)

# Usage
if __name__ == "__main__":
    # Your array of 50 video IDs
    video_ids = ['VmZtY4L7-Us', 'gYpq1_omxOg', 'FzDw07RqCSs', 'UxiiUkQeP4Y', 
             '9-nPAI3FKC4', 'Z072NQHoyew', '0ACj33ZuRdw', 'fsZYkl2eZE4',
             'c0mOukMBQUw', 'sk4iTkZrCio', 'qyZ2XnMPqFU', 'F2KHXITEOyk',
             'YSFpfpE53KA', 'mVWI_tNjfqo', '-78c0VbF_aM', '1FFx3KfWQKQ',
             '1rnvvwpPNmo', 'I7zYxyY7NfU', 'IAjFfVXGJt4', 'V5Mnviy6JTM',
             'OeuOVHL_RmE', 'mZcNt4V7rGA', '1KRBf1L0tOQ', 'Ieo71j-gU1A',
             'iEk86aZbk7w', '9osOUvcktWw', 'NDWnYaMy77o', 'eSfvP7Gv7Gw',
             'FLFTEqrMV0k', 'wkObrT868fA', 'RuoyWcqiCeo', 'eLv5pz10UEM',
             'j9wu1Zn8XmY', 'ZAKqX1vZ1IE', 'O-Fqd1iJm6o', 'cjwm5oCU8eQ',
             'WaD6umPjHhc', 'WmWYMFQpfFk', 'M2nma64bWPk', 'LOo0ZB6BOnQ',
             'prCj0ZEsYhM', 'twsMybtnSSc', 'ogaeRlGLO28', 'vc8qy9bJnNc',
             'PfHLNkR05Mc', 'es34tuBMNSM', 'izPWpcGDZrk', 'DWpmlwZ24Mg',
             'LtPP_mc9kx8', 'K3ejA0b54PU']
    
    # Your Supadata API key
    API_KEY = os.getenv("SUPADATA_API_KEY")
    
    # First, preview the structure and language distribution
    print("Previewing transcript structure and language...")
    preview_transcript_structure(video_ids, API_KEY, sample_size=3)
    
    # Then extract only English transcripts
    print("\nStarting English transcript extraction...")
    extract_transcripts_to_csv(video_ids, API_KEY, "english_video_transcripts.csv", delay=0.5)
    
    print(f"\nAll English transcripts saved to 'english_video_transcripts.csv'")