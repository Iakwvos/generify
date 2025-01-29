import google.generativeai as genai
import json
from flask import current_app
import os

class GeminiService:
    def __init__(self):
        self.model = None
        self.initialize()

    def initialize(self):
        """Initialize Gemini configuration"""
        try:
            if not self.model:
                api_key = os.getenv('GEMINI_API_KEY')
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not found in environment variables")
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash-8b')
        except Exception as e:
            raise Exception(f"Failed to initialize Gemini service: {str(e)}")

    def ensure_initialized(self):
        """Ensure the service is initialized"""
        if not self.model:
            self.initialize()

    def get_insights(self):
        """Get AI-generated insights"""
        try:
            self.ensure_initialized()
            prompt = """Generate 5 insightful tips for e-commerce store optimization.
            Focus on practical, actionable advice that can improve sales and user experience.
            Return the insights as a list of strings."""
            
            response = self.model.generate_content(prompt)
            insights = response.text.strip().split('\n')
            return [insight.strip('*- ') for insight in insights if insight.strip()]
            
        except Exception as e:
            current_app.logger.error(f"Error getting insights: {str(e)}")
            return ["💡 AI insights temporarily unavailable"]

    def _create_prompt(self, url, language):
        """Create a prompt for content generation
        The text in square brackets [] indicates the type of content to generate,
        not the actual content itself."""
        
        sections = [
            ("Product Title", "[Create a short, brand sounding title with ™]"),
            ("sections.main.blocks.reviews_number_wmFXyt.settings.reviews_text", "[x reviews, usually randomly between 300-700]"),
            ("sections.main.blocks.pp_text_VLf9ic.settings.pp_text", "[Summarize the product features and benefits based on the URL content. Aim for 40-50 words.]"),
            ("sections.main.blocks.pp_benefits_Lfapdf.settings.pp_benefits_text1", "[Key features in bullet point, 10-15 words, starting with a ✔️]"),
            ("sections.main.blocks.pp_benefits_Lfapdf.settings.pp_benefits_text2", "[Key features in bullet point, 10-15 words, starting with a ✔️]"),
            ("sections.main.blocks.pp_benefits_Lfapdf.settings.pp_benefits_text3", "[Key features in bullet point, 10-15 words, starting with a ✔️]"),
            ("sections.main.blocks.pp_benefits_Lfapdf.settings.pp_benefits_text4", "[Key features in bullet point, 10-15 words, starting with a ✔️]"),
            ("sections.main.blocks.pp_review_DzipVt.settings.pp_review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.main.blocks.pp_review_DzipVt.settings.pp_review_author_badge_text", "[random full name, from context decide of gender]"),
            ("sections.pp_image_with_benefits_gkXTTj.settings.heading", "[A catchy hook, 5-8 words.]"),
            ("sections.pp_image_with_benefits_gkXTTj.settings.text", "[Provide a brief overview of how the product based on the catchy hook provided before. Aim for 40-50 words.]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7CB6Bn.settings.text", "[key benefit, 8-12 words]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7CB6Bn.settings.heading", "[One word summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7CB6Bn.settings.text]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7CB6Bn.settings.emoji", "[One emoji summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7CB6Bn.settings.text]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7HpQgA.settings.text", "[key benefit, 8-12 words]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7HpQgA.settings.heading", "[One word summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7HpQgA.settings.text]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7HpQgA.settings.emoji", "[One emoji summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7HpQgA.settings.text]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_erNb6q.settings.text", "[key benefit, 8-12 words]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_erNb6q.settings.heading", "[One word summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_erNb6q.settings.text]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_erNb6q.settings.emoji", "[One emoji summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_erNb6q.settings.text]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_gJWaeR.settings.text", "[key benefit, 8-12 words]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_gJWaeR.settings.heading", "[One word summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_gJWaeR.settings.text]"),
            ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_gJWaeR.settings.emoji", "[One emoji summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_gJWaeR.settings.text]"),
            ("sections.pp_image_with_text_BVEaDq.blocks.heading_aFxCRe.settings.heading", "[A text explaining how the product enhances your life in 10-15 words.]"),
            ("sections.pp_image_with_text_BVEaDq.blocks.text_ifpgzE.settings.text", "[Describe the heading from sections.pp_image_with_text_BVEaDq.blocks.heading_aFxCRe.settings.heading. Aim for 40-50 words.]"),
            ("sections.pp_image_with_percentage_fLf47C.blocks.heading_UYwMbc.settings.heading", "[text in style \"Why choose x product?\"]"),
            ("sections.pp_image_with_percentage_fLf47C.blocks.percent_MDgdzN.settings.text", "[first reason why this product is better, 3-5 words.]"),
            ("sections.pp_image_with_percentage_fLf47C.blocks.percent_MDgdzN.settings.percent_value", "[random number between 88-98, saved as integer]"),
            ("sections.pp_image_with_percentage_fLf47C.blocks.percent_DNwFD7.settings.text", "[second reason why this product is better, 3-5 words.]"),
            ("sections.pp_image_with_percentage_fLf47C.blocks.percent_DNwFD7.settings.percent_value", "[random number between 88-98, saved as integer]"),
            ("sections.pp_image_with_percentage_fLf47C.blocks.percent_Wh6UWW.settings.text", "[third reason why this product is better, 3-5 words.]"),
            ("sections.pp_image_with_percentage_fLf47C.blocks.percent_Wh6UWW.settings.percent_value", "[random number between 88-98, saved as integer]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_UYYj4E.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_UYYj4E.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_V7CyvK.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_V7CyvK.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_Z0kjRL.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_Z0kjRL.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_pt5PN0.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_pt5PN0.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_UayexO.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_UayexO.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_pcN8mI.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_pcN8mI.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_FRVTX7.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_FRVTX7.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_AUSNsH.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_AUSNsH.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_gbJSSq.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_gbJSSq.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_325MmR.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_325MmR.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_SqYPOw.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_SqYPOw.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_nJQgxL.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_nJQgxL.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_6WimSV.settings.author_text", "[random full name, from context decide of gender]"),
            ("sections.pp_reviews_dqQHmw.blocks.review_6WimSV.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
            ("sections.pp_comparison_table_ttamEN.blocks.heading_Wjx9pp.settings.heading", "[heading in format \"Why x product and not it's competitor?\"]"),
            ("sections.pp_comparison_table_ttamEN.blocks.text_4ad9ba.settings.text", "[Explanation on why it's better than anything else in the market, 50-70 words]"),
            ("sections.pp_comparison_table_ttamEN.blocks.tableitem_6hMT9z.settings.text", "[1 word of main trait of the product]"),
            ("sections.pp_comparison_table_ttamEN.blocks.tableitem_KNWAfa.settings.text", "[1 word of main trait of the product]"),
            ("sections.pp_comparison_table_ttamEN.blocks.tableitem_jB68ak.settings.text", "[1 word of main trait of the product]"),
            ("sections.pp_comparison_table_ttamEN.blocks.tableitem_CVBp68.settings.text", "[1 word of main trait of the product]"),
            ("sections.pp_comparison_table_ttamEN.blocks.tableitem_6Crhhq.settings.text", "[1 word of main trait of the product]"),
            ("sections.pp_faq_TtURdM.blocks.question_UUEbPG.settings.heading", "[Question regarding this product, 10-15 words]"),
            ("sections.pp_faq_TtURdM.blocks.question_UUEbPG.settings.text", "[Answer to question sections.pp_faq_TtURdM.blocks.question_UUEbPG.settings.text]"),
            ("sections.pp_faq_TtURdM.blocks.question_iwgzRn.settings.heading", "[Question regarding this product, 10-15 words]"),
            ("sections.pp_faq_TtURdM.blocks.question_iwgzRn.settings.text", "[Answer to question sections.pp_faq_TtURdM.blocks.question_iwgzRn.settings.text]"),
            ("sections.pp_faq_TtURdM.blocks.question_gNmdPq.settings.heading", "[Question regarding this product, 10-15 words]"),
            ("sections.pp_faq_TtURdM.blocks.question_gNmdPq.settings.text", "[Answer to question sections.pp_faq_TtURdM.blocks.question_gNmdPq.settings.text]"),
            ("sections.pp_faq_TtURdM.blocks.question_NpRfRa.settings.heading", "[Question regarding this product, 10-15 words]"),
            ("sections.pp_faq_TtURdM.blocks.question_NpRfRa.settings.text", "[Answer to question sections.pp_faq_TtURdM.blocks.question_NpRfRa.settings.text]"),
            ("sections.pp_faq_TtURdM.blocks.question_cwFiY9.settings.heading", "[Question regarding this product, 10-15 words]"),
            ("sections.pp_faq_TtURdM.blocks.question_cwFiY9.settings.text", "[Answer to question sections.pp_faq_TtURdM.blocks.question_cwFiY9.settings.text]")
        ]
        
        language_instructions = {
            'gr': 'Generate all content in Greek language. Use Greek characters and proper Greek grammar/syntax.',
            'en': 'Generate all content in English language.',
            # Add more languages as needed
        }
        
        prompt = f"""URL: {url}
Language Instructions: {language_instructions.get(language, 'Generate in English')}
Output Format: JSON

Instructions: 
1. The text in square brackets [] indicates the type of content to generate, not the actual content itself. 
2. Generate appropriate content based on these instructions.
3. IMPORTANT: Generate ALL content in the specified language ({language}).
4. For reviews, ensure each one is unique and authentic-sounding.
5. Maintain consistent tone and style throughout.

sections = {json.dumps(sections, indent=2)}"""
        
        return prompt, sections

    def _process_chunk_response(self, response_text):
        """Process chunk response and extract JSON"""
        content = response_text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start_idx = content.find("{")
            end_idx = content.rfind("}")
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx + 1]
                return json.loads(json_str)
            raise ValueError("Could not extract valid JSON from response")

    def generate_content(self, url, language):
        """Generate content using Gemini AI with automatic chunk handling"""
        self.ensure_initialized()
        
        prompt, sections = self._create_prompt(url, language)
        result = {}
        
        try:
            # First attempt - try to generate all content at once
            response = self.model.generate_content(prompt)
            result = self._process_chunk_response(response.text)
            
        except Exception as e:
            current_app.logger.warning(f"Full generation failed, switching to chunks: {str(e)}")
            
            # Group similar sections together for better context
            def group_sections(sections):
                groups = []
                current_group = []
                current_type = ""
                
                for section, content in sections:
                    section_type = section.split('.')[0] if '.' in section else section
                    if current_type and section_type != current_type and len(current_group) >= 5:
                        groups.append(current_group)
                        current_group = []
                    current_type = section_type
                    current_group.append((section, content))
                    
                    # Force create new group if current one is too large
                    if len(current_group) >= 5:
                        groups.append(current_group)
                        current_group = []
                
                if current_group:
                    groups.append(current_group)
                return groups
            
            # Process sections in logical groups
            section_groups = group_sections(sections)
            for group in section_groups:
                chunk_prompt = f"""URL: {url}
Language Instructions: {language_instructions.get(language, 'Generate in English')}
Output Format: JSON

Instructions: 
1. The text in square brackets [] indicates the type of content to generate, not the actual content itself. 
2. Generate appropriate content based on these instructions.
3. IMPORTANT: Generate ALL content in the specified language ({language}).
4. For reviews, ensure each one is unique and authentic-sounding.
5. Maintain consistent tone and style throughout.

sections = {json.dumps(group, indent=2)}"""
                
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        response = self.model.generate_content(chunk_prompt)
                        chunk_result = self._process_chunk_response(response.text)
                        
                        # Process each section in the chunk
                        for section, content in chunk_result.items():
                            if isinstance(content, dict):
                                if section not in result:
                                    result[section] = {}
                                result[section].update(content)
                            elif isinstance(content, list):
                                if section not in result:
                                    result[section] = []
                                result[section].extend(content)
                            else:
                                result[section] = content
                        
                        break
                    except Exception as chunk_error:
                        current_app.logger.error(f"Group generation failed (attempt {retry + 1}): {str(chunk_error)}")
                        if retry == max_retries - 1:
                            for section, _ in group:
                                if section not in result:
                                    result[section] = "[Content generation failed]"
                        continue
        
        # Ensure all sections are present in the result
        for section, _ in sections:
            if section not in result:
                result[section] = "[Content not generated]"
        
        return result 