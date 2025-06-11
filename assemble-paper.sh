#!/bin/bash

# Assemble complete research paper from sections
# Usage: ./assemble-paper.sh [output-file]

OUTPUT_FILE=${1:-"complete-research-paper.md"}
SECTIONS_DIR="paper-sections"

echo "Assembling research paper sections into: $OUTPUT_FILE"

# Start with the header and abstract from main file
head -7 research-paper.md > "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Add each section in order
for i in {1..6}; do
    section_file="$SECTIONS_DIR/0$i-*.md"
    if ls $section_file 1> /dev/null 2>&1; then
        echo "Adding section $i..."
        echo "" >> "$OUTPUT_FILE"
        echo "# $i. $(basename $section_file .md | sed 's/^[0-9][0-9]-//' | sed 's/-/ /g' | sed 's/\b\w/\U&/g')" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        cat $section_file >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "---" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    else
        echo "Warning: Section $i not found"
    fi
done

# Add comprehensive references from references.md
if [ -f "references.md" ]; then
    echo "Adding comprehensive references..."
    echo "" >> "$OUTPUT_FILE"
    cat references.md >> "$OUTPUT_FILE"
else
    echo "Warning: references.md not found, adding basic references"
    echo "# References" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "- Van der Aalst, W.M.P. (1998). \"The Application of Petri Nets to Workflow Management.\" Journal of Circuits, Systems and Computers" >> "$OUTPUT_FILE"
    echo "- Murata, T. (1989). \"Petri nets: Properties, analysis and applications.\" Proceedings of the IEEE" >> "$OUTPUT_FILE"
    echo "- Dumas, M., et al. (2018). \"Fundamentals of Business Process Management.\" Springer" >> "$OUTPUT_FILE"
    echo "- Russell, N., et al. (2005). \"Workflow patterns: Identification, representation and tool support.\" Conceptual Modeling–ER 2005" >> "$OUTPUT_FILE"
fi

echo "Complete paper assembled as: $OUTPUT_FILE"
echo "Word count: $(wc -w < "$OUTPUT_FILE") words"