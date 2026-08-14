package org.schuss.legacy.ksoloti;

import java.io.IOException;
import java.io.StringWriter;
import java.io.Writer;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/** Minimal deterministic JSON writer for the bridge's versioned JSONL records. */
final class StableJson {
    private StableJson() {
    }

    static String stringify(Object value) {
        StringWriter output = new StringWriter();
        try {
            write(value, output);
        } catch (IOException exception) {
            throw new IllegalStateException("StringWriter unexpectedly failed", exception);
        }
        return output.toString();
    }

    static void write(Object value, Writer out) throws IOException {
        if (value == null) {
            out.write("null");
        } else if (value instanceof String text) {
            writeString(text, out);
        } else if (value instanceof Boolean || value instanceof Byte
                || value instanceof Short || value instanceof Integer
                || value instanceof Long) {
            out.write(value.toString());
        } else if (value instanceof Float number) {
            if (!Float.isFinite(number)) {
                throw new IllegalArgumentException("JSON does not support non-finite numbers");
            }
            out.write(number.toString());
        } else if (value instanceof Double number) {
            if (!Double.isFinite(number)) {
                throw new IllegalArgumentException("JSON does not support non-finite numbers");
            }
            out.write(number.toString());
        } else if (value instanceof Map<?, ?> map) {
            writeMap(map, out);
        } else if (value instanceof List<?> list) {
            writeList(list, out);
        } else {
            throw new IllegalArgumentException("Unsupported JSON value: " + value.getClass().getName());
        }
    }

    private static void writeMap(Map<?, ?> map, Writer out) throws IOException {
        TreeMap<String, Object> sorted = new TreeMap<>();
        for (Map.Entry<?, ?> entry : map.entrySet()) {
            if (!(entry.getKey() instanceof String key)) {
                throw new IllegalArgumentException("JSON object keys must be strings");
            }
            sorted.put(key, entry.getValue());
        }
        out.write('{');
        boolean first = true;
        for (Map.Entry<String, Object> entry : sorted.entrySet()) {
            if (!first) {
                out.write(',');
            }
            first = false;
            writeString(entry.getKey(), out);
            out.write(':');
            write(entry.getValue(), out);
        }
        out.write('}');
    }

    private static void writeList(List<?> list, Writer out) throws IOException {
        out.write('[');
        boolean first = true;
        for (Object value : list) {
            if (!first) {
                out.write(',');
            }
            first = false;
            write(value, out);
        }
        out.write(']');
    }

    private static void writeString(String text, Writer out) throws IOException {
        out.write('"');
        for (int offset = 0; offset < text.length();) {
            int codePoint = text.codePointAt(offset);
            offset += Character.charCount(codePoint);
            switch (codePoint) {
                case '"' -> out.write("\\\"");
                case '\\' -> out.write("\\\\");
                case '\b' -> out.write("\\b");
                case '\f' -> out.write("\\f");
                case '\n' -> out.write("\\n");
                case '\r' -> out.write("\\r");
                case '\t' -> out.write("\\t");
                default -> {
                    if (codePoint < 0x20 || codePoint == 0x2028 || codePoint == 0x2029) {
                        out.write(String.format("\\u%04x", codePoint));
                    } else {
                        out.write(Character.toChars(codePoint));
                    }
                }
            }
        }
        out.write('"');
    }
}
