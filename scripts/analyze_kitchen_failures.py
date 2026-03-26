import json

def main():
    # Load results
    with open('results/gemini_stratified_400.json') as f:
        data = json.load(f)

    predictions = data['predictions']

    # Filter for ground truth = kitchen
    kitchen_failures = [p for p in predictions if p['ground_truth'] == 'kitchen' and p['prediction'] != 'error' and not p['correct']]

    print(f'Total Valid Kitchen Predictions (that were wrong): {len(kitchen_failures)}')

    # Show a sample of raw responses
    print('\n=== RAW RESPONSES FOR KITCHENS (Sample of 10) ===')
    for i, p in enumerate(kitchen_failures[:10]):
        print(f'\nSample {i+1}:')
        print(f'  Prediction Parsed: {p["prediction"]}')
        print(f'  Raw Response:\n{p["raw_response"]}')

    # Analyze if "kitchen" appears ANYWHERE in the raw response
    kitchen_mentions = 0
    for p in kitchen_failures:
        if 'kitchen' in p['raw_response'].lower():
            kitchen_mentions += 1
            print(f'\nFOUND KITCHEN IN RAW TEXT (but parsed as {p["prediction"]}):')
            print(p['raw_response'])

    print(f'\n=== KEYWORD ANALYSIS ===')
    print(f'Number of failed samples where "kitchen" appears in raw text: {kitchen_mentions}/{len(kitchen_failures)}')

if __name__ == "__main__":
    main()
