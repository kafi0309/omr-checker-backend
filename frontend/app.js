const languageSelect = document.getElementById('language');
const correctAnswersInput = document.getElementById('correctAnswers');
const correctAnswersLabel = document.getElementById('correctAnswersLabel');
const numQuestionsInput = document.getElementById('numQuestions');
const checkButton = document.getElementById('checkButton');
const resultArea = document.getElementById('result');
const answerSheetImageInput = document.getElementById('answerSheetImage');

// Update placeholder and label on language change
languageSelect.addEventListener('change', () => {
  if (languageSelect.value === 'eng') {
    correctAnswersLabel.textContent = 'Correct Answers (e.g. ABCD...):';
    correctAnswersInput.placeholder = 'Example: ABCDABCD...';
  } else {
    correctAnswersLabel.textContent = 'সঠিক উত্তর (যেমন: কখগঘ...):';
    correctAnswersInput.placeholder = 'উদাহরণ: কখগঘকখ...';
  }
});

// Validate answers
function validateAnswers(answers, lang) {
  if (lang === 'eng') {
    return /^[ABCDabcd]+$/.test(answers);
  } else {
    return /^[কখগঘ]+$/.test(answers);
  }
}

checkButton.addEventListener('click', async (event) => {
  event.preventDefault();

  const numQuestions = parseInt(numQuestionsInput.value);
  const correctAnswers = correctAnswersInput.value.trim().toUpperCase(); // convert to uppercase
  const language = languageSelect.value;
  const file = answerSheetImageInput.files[0];

  resultArea.textContent = '';

  if (isNaN(numQuestions) || numQuestions < 1) {
    resultArea.textContent = language === 'eng'
      ? 'Please enter a valid number of questions.'
      : 'দয়া করে বৈধ প্রশ্ন সংখ্যা লিখুন।';
    return;
  }

  if (correctAnswers.length !== numQuestions) {
    resultArea.textContent = language === 'eng'
      ? `Number of answers (${correctAnswers.length}) does not match number of questions (${numQuestions}).`
      : `উত্তরের সংখ্যা (${correctAnswers.length}) প্রশ্নের সংখ্যার (${numQuestions}) সাথে মেলে না।`;
    return;
  }

  if (!validateAnswers(correctAnswers, language)) {
    resultArea.textContent = language === 'eng'
      ? 'Correct answers contain invalid characters. Allowed: A, B, C, D'
      : 'সঠিক উত্তরে অবৈধ অক্ষর রয়েছে। অনুমোদিত: ক, খ, গ, ঘ';
    return;
  }

  if (!file) {
    resultArea.textContent = language === 'eng'
      ? 'Please upload an answer sheet image.'
      : 'অনুগ্রহ করে উত্তরপত্রের ছবি আপলোড করুন।';
    return;
  }

  const formData = new FormData();
  formData.append('correct_answers', correctAnswers);
  formData.append('language', language);
  formData.append('image', file);

  try {
    const response = await fetch('http://192.168.1.2:5000/check-answers', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();

    let message = '';
    message += language === 'eng'
      ? `Total Questions: ${data.total_questions}\nCorrect Answers: ${data.correct_count}\nIncorrect Questions: ${data.incorrect_questions.length > 0 ? data.incorrect_questions.join(', ') : 'None'}\n`
      : `মোট প্রশ্ন: ${data.total_questions}\nসঠিক উত্তর: ${data.correct_count}\nভুল প্রশ্ন: ${data.incorrect_questions.length > 0 ? data.incorrect_questions.join(', ') : 'কোনো নেই'}\n`;
    message += `\n${data.message}`;

    resultArea.textContent = message;

  } catch (error) {
    resultArea.textContent = language === 'eng'
      ? `Error: ${error.message}`
      : `ত্রুটি: ${error.message}`;
  }
});

