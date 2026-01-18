"""
Sample Help Center articles for RAG chatbot.

Per assignment requirements: "Please note that we do not require you to actively crawl 
the provided URLs, we are interested in the content itself!"

This module contains the actual content from the two required Typeform Help Center articles,
structured as Article objects for the RAG pipeline. This approach:
- Avoids 403 errors from active web scraping
- Ensures consistent, reliable content for the RAG system  
- Follows the assignment's explicit permission to not actively crawl URLs
- Allows for controlled preprocessing and chunking

The content below was fetched from the official Typeform Help Center URLs on 2026-01-18
and preserved in its original form for accurate retrieval and response generation.
"""
from data_ingestion import Article
from typing import List


def load_sample_articles() -> List[Article]:
    """
    Load the two required Typeform Help Center articles.
    
    Articles:
    1. Create multi-language forms
    2. Add a Multi-Question Page to your form
    
    Returns a list of Article objects with the full Help Center content.
    """
    articles = [
        Article(
            url="https://help.typeform.com/hc/en-us/articles/23541138531732-Create-multi-language-forms",
            title="Create multi-language forms",
            content="""
Save time and reach a wider audience by creating a single form with multiple language options. 
You'll have the option to write your own translations or have AI translate your form for you. 
Depending on your language settings, you can decide if you want to automatically have your form 
translated for respondents or give them the option to translate the form. The form will be 
translated if the respondent's browser language matches one of the translations you've added. 
All responses will be displayed in one place within your Results panel.

You can create multi-language forms with the following languages: Arabic, Catalan, Chinese 
(simplified), Chinese (traditional), Croatian, Danish, Dutch, English, Estonian, Finnish, 
French, German (formal), German (informal), Greek, Hebrew, Hungarian, Italian, Japanese, 
Korean, Norwegian, Polish, Portuguese, Russian, Spanish, Swedish, Turkish, and Ukrainian.

To create multi-language forms, you'll need a Business, Talent, Growth Pro, Growth Custom, 
or Enterprise plan.

We recommend finalizing the text in your form before adding any translations, as this could 
cause your translations to not match any edited text. If you do need to edit your form, you 
can always go back and edit your translations to include any changed text.

## Add multiple languages to your form

1. Open your form and click the Translations icon.
2. Click + Add languages.
3. Select the languages you'd like to add to your form. Then click Add when you're done.

Respondents will only see the banner asking if they want to translate the form if their 
browser language matches one of the languages you've chosen for translations.

4. Next, you'll see the status Translation needed for the language you selected.

Hover over the language you've added and you can choose how you'd like to translate your form:
- You can Translate with AI.
- Or Download a template.

In our example, we'll select Translate with AI. Then, if needed, we can edit the translations 
that were provided by AI.

After clicking Translate with AI, you'll see the status has changed to Translated.

If you're happy to use the translations provided by AI, you can click Publish and your form 
is ready to go. However, if you'd like to edit the translations provided by AI move on to 
the next section.

## Edit the translations provided by AI

1. Click Download template. This will download the latest stored translation in a CSV file.

In our example, it'll download the translations AI provided for Hungarian.

2. Next, open the CSV file. We'll use Google Sheets to open our CSV file.

The CSV file contains the following 3 columns:
• id - This column contains the ids of fields that have text in the form.
• original - This column lists the text in your form for questions, statements, answer 
  options, and buttons in the original language.
• translation - This column lists the corresponding translations provided by AI.

3. Edit any of the translations in the translation column.

Here are a few things to keep in mind when editing translations:
• You can only edit text in the translation column. If you edit any of the other columns, 
  you'll receive an error message when you upload the CSV back into Typeform.
• All of the cells in the translations column must be completed. For example, if you have 
  15 cells in the original column with text, all 15 cells in the translation column must 
  be filled in.
• The number of rows must remain the same number from when you downloaded the template. 
  You can't add additional rows to the CSV.

4. Download the edited translation template as a CSV file.

5. Head back to your Typeform account and click Upload template. Only CSV files are supported.

A pop-up will appear to let you know that uploading a new translation will replace your 
current translation file. Click Upload translation.

Select the new CSV file you downloaded from step 8 and click Open.

6. When you've finished uploading your new translations. Click Save or Publish edits to make 
your changes live.

If you edit the text in your form in the Content panel after you've uploaded a translation, 
you'll see a notification letting you know that your form has changed and you'll need to 
update your translations.

Click the Translations icon in the toolbar to update your translations. The status of your 
language will display as Update required. Select how you'd like to update your translations.

To delete a translation, click the trash can icon.

If you've made any edits or updates to your form, make sure you click Publish to make your 
changes live.

## Choose your language settings on how translations will be displayed

By default, if a respondent's browser language matches one of the languages you've chosen 
for translation, the form will automatically be translated for them.

If you would like to give respondents the option to translate the form, they'll see a banner 
at the top of the form, asking if they want it to be translated. This banner will only appear 
if their browser language matches one of the languages you've chosen for translation. For 
instance, if your form is in English and you've selected Spanish as a translated language, 
Spanish-speaking respondents with their browser language set to Spanish will see the banner 
asking if they want the form to be translated into Spanish.

Choose your language settings:

1. Open your form and click the settings icon in the tool bar.
2. Select Language.
3. Under Translations, toggle Automatically translate to match browser language to be on or 
   off. This is toggled on by default. Then click Save when done.

If you've chosen to toggle off Automatically translate to match browser language, respondents 
will see a banner at the top of the screen asking them if they would like to translate the 
form to the language they have set for their browser.

When respondents click the Translate button, the form will then appear in their browser's 
set language.

## Force translations based on URL parameters

Once you've set up translations in your form as described above, this feature allows you to 
control the language translation displayed to respondents by adding a URL parameter to their 
form link.

Instead of forms automatically showing translations based on a respondent's browser language 
settings, you can force a specific language to appear by adding a parameter to the form URL.

This ensures consistency when you know which geographic region will receive your form, and 
maintains brand consistency when embedding forms in websites—the form will match your site's 
language.

Add ?typeform-lang=xxxxx if it's the first URI query parameter, or &typeform-lang=xxxxx if 
it's not the first URI query parameter to your form URL, where "xxxxx" is the language code.

For example:
https://yourform.typeform.com/to/FormID?typeform-lang=es (for Spanish)

if typeform-lang is the first parameter you're adding to the form, or

https://yourform.typeform.com/to/FormID#first_name=xxxxx&typeform-lang=es

if you're already using other URL parameters in your form.

The Iso Codes of the supported languages that you can add to the form URL are:
ar: arabic, ca: catalan, ch: chinese (simplified), cs: czech, da: danish, de: german (formal), 
di: german (informal), el: greek, en: english, es: spanish, et: estonian, fi: finnish, 
fr: french, he: hebrew, hr: croatian, hu: hungarian, it: italian, ja: japanese, ko: korean, 
nl: dutch, no: norwegian, pl: polish, pt: portuguese, ru: russian, sv: swedish, tr: turkish, 
uk: ukrainian, zh: chinese (traditional).

Make sure to set up translation languages in your form first because forcing translations 
based on URL parameters only works for languages already set up in the form.

## FAQ

### How can I see the translations provided?

You'll be able to see the translations of your form if your browser's language is set to 
one of the translated languages you've selected for your form.

As a workaround, you can change the language settings of your browser to see the translations 
of your form. For example, if you've selected Spanish as one of the translated languages, you 
can set your browser's language to Spanish and then you'll be able to see the translations 
provided.

### Can I edit the translations?

Yes, you can edit translations by downloading the CSV template. Then edit the translations 
in the translations columns and re-upload the CSV file back into Typeform. Advanced users 
can edit translations through our API.

Keep in mind that if you edit translations and then later duplicate your form, the copy of 
your form won't contain the edited translations.

### How long will it take for my form to be translated?

Translations can take about 10-15 seconds to load. If your form is very long, or the questions 
in your form are very wordy, it could take longer. Occasionally, translations may fail if the 
request is too large.

### What language will my responses be shown in?

Responses for close-ended question types (Multiple Choice, Dropdown, etc.) will be shown in 
the main language you've selected. Responses for open-ended question types (Short Text, Long 
Text, etc.) will be in the language respondents have entered their answers in.

### Are there any limitations with translating large forms?

If you're using the option to translate your form with AI, there are a few limitations:

If your form's main language is set to English, there are no limitations, unless you have 
one or more of the following in your form:
• The form has more than one hyperlinked URL.
• The form has more than 100 answer options within one question, or if the form has a 
  Question Group with more than 100 answer options.
• The form contains Variables or URL parameters.

If your form contains one or more of the above items, we recommend following the limit 
suggestions for forms set to a non-English language.

If your form's main language is set to a non-English language, we recommend the following 
limits on your form:
• 20 questions without answer options or up to 10 answer options from Multiple Choice, 
  Dropdown, Picture Choice, Yes/No, or Legal question types.
• 10 questions of any type with up to 20 answer options.
• 200 words in your form. This can be any text you've entered in your form, such as question 
  text, labels for Picture Choice options, Welcome Screen, etc.

If you've exceeded the recommended limits listed above, this can cause an error when you 
generate translations with AI. You can however, download the CSV template of your form, 
manually enter all of the translations, and then re-upload the CSV.

### How does multi-language forms work with embeds?

Multi-language forms will work with forms that are embedded on a website. However, 
Multi-language forms won't work if you've embedded the form in an email.

### Why has part of my form not been translated?

If you've manually edited a translation and uploaded it as a CSV file, but some parts aren't 
translated when you view your form in another language, check the question text. A comma at 
the end of a question field (for example, "Hello Maria,") can prevent either the question 
itself or the related text in the description field from being translated.

This happens because text ending with a comma can be misread during the CSV import process, 
depending on how the file was exported.

To fix this issue, use one of these options:
• Add a space after the comma: Hello Maria, [add space here]
• Remove the comma: Hello Maria
• Use a period instead: Hello Maria.

Any of these will ensure the translation works correctly.
            """,
            metadata={
                "title": "Create multi-language forms",
                "url": "https://help.typeform.com/hc/en-us/articles/23541138531732-Create-multi-language-forms",
                "source": "typeform_help_center"
            }
        ),
        Article(
            url="https://help.typeform.com/hc/en-us/articles/27703634781076-Add-a-Multi-Question-Page-to-your-form",
            title="Add a Multi-Question Page to your form",
            content="""
Traditionally, our forms have been designed to show one question at a time. This makes them 
feel more conversational and increases engagement. But sometimes, you might want to streamline 
your form by asking multiple questions on the same page. By adding a Multi-Question Page to 
your form, you can do just that.

## Supported question types

The Multi-Question Page supports the following question types:
• Checkbox
• Date
• Dropdown
• Email
• Legal
• Long Text
• Multiple Choice
• NPS
• Number
• Opinion Scale
• Phone Number
• Ranking
• Rating
• Short Text
• Statement
• Website
• Yes/No

## How to add a Multi-Question Page to your form

1. Go to the form you want to edit and click + Add content.

2. Select Multi-Question Page from the question menu.

Note! If you don't see Multi-Question Page in the content menu, please follow the instructions 
in this article on how to add multiple questions to a form page.

3. A new page will be added to your form where you can add as many questions as you like. To 
begin with, write your question header and a description.

Note! The question header of your Multi-Question Page won't be included in downloaded results. 
You'll only see results for each question within your Multi-Question Page. This is because 
the header doesn't collect results from your respondents.

4. Click the dropdown arrow next to your header. You'll notice a Short Text question has been 
added automatically.

If you want to change the question type from Short Text to another question type, go to the 
question settings in the right-hand sidebar and choose a question type from the dropdown menu.

5. Write your first question.

6. Then click + Add content to add another question.

7. You can change your question settings in the right-hand sidebar. For example, depending on 
your question type, you can make the question required or set a character limit for responses.

8. Once you've added all the questions you want, you're done!

If you want to add more questions to your form outside of the Multi-Question page, click + 
Add content and select a question type.

If you select a question type that's compatible with the Multi-Question Page (see the top of 
this article for a full list of supported question types), it'll be placed in the 
Multi-Question Page by default, but you can move it by clicking and dragging it out of the 
Multi-Question Page.

You can also click on the question type icons and drag them around to change the order within 
the Multi-Question Page.

Similarly, you can drag and drop compatible question types into your Multi-Question Page.

9. If you want to add logic to your form, head to the Workflow panel to add Branching rules 
and conditions to your Multi-Question Page.

You can select the individual questions within your Multi-Question page to send your 
respondents down different paths or to segment your audience.

And voilà! Here's how our Multi-Question Page will look to our respondents.

10. Once you've collected some responses, go to the Results panel to see your data. Answers 
to each question on a Multi-Question Page will be shown as standalone answers in your results, 
just like in forms with only one question per page.

11. Similarly, when you connect a form containing a Multi-Question Page to another tool, it 
works just like with any other question type. You can map each question from the 
Multi-Question Page to a different field in the integration.

Check out all our integrations here.

## FAQ

#### Can I add a Partial Submit Point after the Multi-Question Page?

You can add a Partial Submit Point after the Multi-Question Page, just like with any other 
question type. However, you can't add a Partial Submit Point after a specific question within 
your Multi-Question Page.

#### Does the Multi-Question Page support Data Enrichment?

Yes. You can collect enrichment data with an email question in the Multi-Question Page if it 
is the first email question of your form.

#### Can I use Logic with the Multi-Question Page?

Yes. You can use Logic to direct respondents to a Multi-Question page or use answers provided 
in the Multi-Question Page in Logic rules.

#### Can I add a score or create an outcome quiz with the Multi-Question Page?

No. Currently, adding a score or creating an outcome quiz is not supported with the 
Multi-Question Page.

If you want to create an umbrella question with sub-questions on separate pages, check out 
our Question Group feature.

#### Can I embed a Multi-Question Page in an email?

No. Launching your form in an email with the Multi-Question Page as your first question is 
currently not supported.
            """,
            metadata={
                "title": "Add a Multi-Question Page to your form",
                "url": "https://help.typeform.com/hc/en-us/articles/27703634781076-Add-a-Multi-Question-Page-to-your-form",
                "source": "typeform_help_center"
            }
        )
    ]
    
    return articles
