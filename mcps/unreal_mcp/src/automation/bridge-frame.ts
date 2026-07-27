export function getRawDataByteLength(data: unknown): number {
    if (typeof data === 'string') {
        return Buffer.byteLength(data, 'utf8');
    }

    if (Buffer.isBuffer(data)) {
        return data.length;
    }

    if (Array.isArray(data)) {
        return data.reduce((total, item) => total + (Buffer.isBuffer(item) ? item.length : 0), 0);
    }

    if (data instanceof ArrayBuffer) {
        return data.byteLength;
    }

    if (ArrayBuffer.isView(data)) {
        return data.byteLength;
    }

    return 0;
}

export function rawDataToUtf8String(data: unknown, byteLengthHint?: number): string {
    if (typeof data === 'string') {
        return data;
    }

    if (Buffer.isBuffer(data)) {
        return data.toString('utf8');
    }

    if (Array.isArray(data)) {
        const buffers = data.filter((item): item is Buffer => Buffer.isBuffer(item));
        const totalLength = typeof byteLengthHint === 'number'
            ? byteLengthHint
            : buffers.reduce((total, item) => total + item.length, 0);
        return Buffer.concat(buffers, totalLength).toString('utf8');
    }

    if (data instanceof ArrayBuffer) {
        return Buffer.from(data).toString('utf8');
    }

    if (ArrayBuffer.isView(data)) {
        return Buffer.from(data.buffer, data.byteOffset, data.byteLength).toString('utf8');
    }

    return '';
}
