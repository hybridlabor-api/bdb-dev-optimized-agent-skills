const CLASS_START_PATTERN = /\b(?:class|struct)\s+\w+[^;{]*\{/g;

function isIdentifierCharacter(character) {
  return character !== undefined && /[A-Za-z0-9_]/.test(character);
}

function hasRawStringPrefix(source, index) {
  const previous = source[index - 1];
  if (!isIdentifierCharacter(previous)) return true;
  if (
    (previous === 'L' || previous === 'u' || previous === 'U')
    && !isIdentifierCharacter(source[index - 2])
  ) {
    return true;
  }
  return source.slice(index - 2, index) === 'u8'
    && !isIdentifierCharacter(source[index - 3]);
}

function rawStringEnd(source, index) {
  if (
    source[index] !== 'R'
    || source[index + 1] !== '"'
    || !hasRawStringPrefix(source, index)
  ) {
    return undefined;
  }

  const delimiterStart = index + 2;
  let openParenthesis = delimiterStart;
  while (openParenthesis < source.length && source[openParenthesis] !== '(') {
    const character = source[openParenthesis];
    if (
      openParenthesis - delimiterStart >= 16
      || character === '\\'
      || character === ')'
      || /\s/.test(character)
    ) {
      return undefined;
    }
    openParenthesis += 1;
  }
  if (source[openParenthesis] !== '(') return undefined;

  const delimiter = source.slice(delimiterStart, openParenthesis);
  const terminator = `)${delimiter}"`;
  const terminatorStart = source.indexOf(terminator, openParenthesis + 1);
  return terminatorStart < 0
    ? source.length - 1
    : terminatorStart + terminator.length - 1;
}

function maskRange(masked, source, start, end) {
  for (let index = start; index <= end; index += 1) {
    const character = source[index];
    masked[index] = character === '\n' || character === '\r' ? character : ' ';
  }
}

function isContinuedCommentLine(source, newlineIndex) {
  if (source[newlineIndex] === '\r') return source[newlineIndex - 1] === '\\';
  return source[newlineIndex - 1] === '\\'
    || (source[newlineIndex - 1] === '\r' && source[newlineIndex - 2] === '\\');
}

function maskTypeScriptSource(source, maskLiterals) {
  const masked = source.split('');
  let mode = 'code';
  let quote = '';

  for (let index = 0; index < source.length; index += 1) {
    const character = source[index];
    const nextCharacter = source[index + 1];

    if (mode === 'code') {
      if (character === '"' || character === "'" || character === '`') {
        mode = 'quoted';
        quote = character;
        if (maskLiterals) masked[index] = ' ';
      } else if (character === '/' && nextCharacter === '/') {
        mode = 'line-comment';
        masked[index] = ' ';
        masked[index + 1] = ' ';
        index += 1;
      } else if (character === '/' && nextCharacter === '*') {
        mode = 'block-comment';
        masked[index] = ' ';
        masked[index + 1] = ' ';
        index += 1;
      }
      continue;
    }

    if (mode === 'quoted') {
      if (maskLiterals) {
        masked[index] = character === '\n' || character === '\r' ? character : ' ';
      }
      if (character === '\\' && nextCharacter !== undefined) {
        if (maskLiterals) {
          masked[index + 1] = nextCharacter === '\n' || nextCharacter === '\r'
            ? nextCharacter
            : ' ';
        }
        index += 1;
      } else if (character === quote) {
        mode = 'code';
        quote = '';
      }
      continue;
    }

    if (mode === 'line-comment') {
      if (character === '\n' || character === '\r') {
        mode = 'code';
      } else {
        masked[index] = ' ';
      }
      continue;
    }

    masked[index] = character === '\n' || character === '\r' ? character : ' ';
    if (character === '*' && nextCharacter === '/') {
      masked[index + 1] = ' ';
      index += 1;
      mode = 'code';
    }
  }

  return masked.join('');
}

export function maskTypeScriptComments(source) {
  return maskTypeScriptSource(source, false);
}

export function maskTypeScriptLiteralsAndComments(source) {
  return maskTypeScriptSource(source, true);
}

export function maskCppLiteralsAndComments(source) {
  const masked = source.split('');
  let mode = 'code';
  let quote = '';

  for (let index = 0; index < source.length; index += 1) {
    const character = source[index];
    const nextCharacter = source[index + 1];

    if (mode === 'code') {
      const rawEnd = rawStringEnd(source, index);
      if (rawEnd !== undefined) {
        maskRange(masked, source, index, rawEnd);
        index = rawEnd;
      } else if (character === '"' || character === "'") {
        mode = 'quoted';
        quote = character;
        masked[index] = ' ';
      } else if (character === '/' && nextCharacter === '/') {
        mode = 'line-comment';
        masked[index] = ' ';
        masked[index + 1] = ' ';
        index += 1;
      } else if (character === '/' && nextCharacter === '*') {
        mode = 'block-comment';
        masked[index] = ' ';
        masked[index + 1] = ' ';
        index += 1;
      }
      continue;
    }

    if (mode === 'quoted') {
      masked[index] = character === '\n' || character === '\r' ? character : ' ';
      if (character === '\\' && nextCharacter !== undefined) {
        masked[index + 1] = nextCharacter === '\n' || nextCharacter === '\r'
          ? nextCharacter
          : ' ';
        index += 1;
      } else if (character === quote) {
        mode = 'code';
        quote = '';
      }
      continue;
    }

    if (mode === 'line-comment') {
      if (character === '\n' || character === '\r') {
        if (!isContinuedCommentLine(source, index)) mode = 'code';
      } else {
        masked[index] = ' ';
      }
      continue;
    }

    masked[index] = character === '\n' || character === '\r' ? character : ' ';
    if (character === '*' && nextCharacter === '/') {
      masked[index + 1] = ' ';
      index += 1;
      mode = 'code';
    }
  }

  return masked.join('');
}

function closingBraceIndex(codeSource, openBrace) {
  let depth = 0;
  for (let index = openBrace; index < codeSource.length; index += 1) {
    if (codeSource[index] === '{') depth += 1;
    if (codeSource[index] === '}') {
      depth -= 1;
      if (depth === 0) return index;
    }
  }
  return undefined;
}

export function enclosingClassSource(source, memberIndex) {
  const codeSource = maskCppLiteralsAndComments(source);
  const classMatches = [...codeSource.slice(0, memberIndex).matchAll(CLASS_START_PATTERN)];
  for (const classMatch of classMatches.reverse()) {
    if (classMatch.index === undefined) continue;
    const openBrace = classMatch.index + classMatch[0].lastIndexOf('{');
    const closeBrace = closingBraceIndex(codeSource, openBrace);
    if (closeBrace !== undefined && closeBrace < memberIndex) continue;
    return source.slice(classMatch.index, closeBrace === undefined ? undefined : closeBrace + 1);
  }
  return source;
}
