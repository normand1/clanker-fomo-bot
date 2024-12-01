import anthropic
from database import DatabaseManager  # Import the DatabaseManager class


class TokenAnalyzer:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.db_manager = DatabaseManager()  # Instantiate the DatabaseManager

    def analyze_tokens(self, token_list: str, top_x: int) -> dict:
        """
        Analyzes a list of tokens using Claude to identify themes and patterns.

        Args:
            token_list (str): Comma-separated list of tokens to analyze

        Returns:
            dict: Dictionary containing the theme analysis and themes list
        """
        message = self.client.messages.create(
            model="claude-3-5-sonnet-latest",  # claude-3-5-haiku-20241022
            max_tokens=1000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": '<examples>\n<example>\n<TOKEN_LIST>\nAIMEME,HELLYEAH,Unknown,HACIENDA,AUTISTIC WIGGER INTERNET MONIES,BRICS Currency,DAOAshe,Hello December,Tamvan,GINGY,One Shot,bankr,KOALITION,ORB,$Off-Grid,uzi,Torre LATAM,huh dog,Arcane,I\'ll be back,univers,Houdini AI,JEWINYU,Heartbreak,Bictoin,bigbaseballs,DWN,DEGEGEN,FreeHouse,Mexican Coke,AADRAWING,SquiMeme,Noodle,bee,From the director of comic sans,GAWX,Bath Time,crows zero,David Mayer,Clank Griswold,ADCEDOK,Kinetix,Science Acceleration,LOL,$SISCO,Gang Bang,Gamestop on Clanker,based inu,Pigeon,DJmodli,Don\'t buy This,A BiLLON CCARELLA,Move2Earn,Doom,ChickenDog,VirtualsClankerSpectralAIagentlayerFarcastAIFUNSimmi,Carfaster,duma,WE OUTSIDE,Spice Melange,For The Culture,Hot Pockets and Coconut Water,✩₊˚.⋆☾⋆⁺₊✧,Lwo,AIMEME,HELLYEAH,CLANKER,HACIENDA,AUTISTICWIGGER,BRICS,DAOAshe,DECEMBER,TMVN,5G,ONESHOT,bankr,KOAL,ORB,OG,UZI,LATAM,DHUH,ARC,BACK,univers,HOUDINI,JEWINYU,HEARTBREAK,BCT,BIGBASEBALLS,DWN,DGN,FrHo,COMX,AADWR,SQME,$Noodle,BUZZ,PAPYRUS,GAWX,BATH,crows zero,TABOO,clankgriswold,ADCEDOK,KINETIX,SCI/ACC,LOL,SISCO,BANG,GME,binu,Pg,DJmo,DBT,ABC,M2E,IDDQD,CHID,BASEAI,LAMBO,duma,OUTSIDE,SPICE,FTC,HPCW,✩˚☾⋆✧,LWO\n</TOKEN_LIST>\n<ideal_output>\nI\'ll analyze the tokens and group them into specific themes. Here\'s my categorization:\n\n<themed_dictionary>\n{\n    "AI-focused Drawing and Creation": ["AADRAWING", "AADWR", "Houdini AI", "HOUDINI"],\n    \n    "Dog-themed Meme Tokens": ["ChickenDog", "CHID", "huh dog", "DHUH"],\n    \n    "Food and Beverage References": ["Mexican Coke", "Hot Pockets and Coconut Water", "HPCW", "Noodle", "$Noodle"],\n    \n    "Gaming Reference Tokens": ["Doom", "IDDQD", "Gamestop on Clanker", "GME"],\n    \n    "Cultural Movement Tokens": ["For The Culture", "FTC", "WE OUTSIDE", "OUTSIDE"],\n    \n    "Science and Technology Innovation": ["Science Acceleration", "SCI/ACC", "5G"],\n    \n    "Typography and Font References": ["From the director of comic sans", "PAPYRUS", "COMX"],\n    \n    "Latin American Focused": ["Torre LATAM", "LATAM", "HACIENDA"],\n    \n    "Classic Movie References": ["I\'ll be back", "BACK", "Clank Griswold", "clankgriswold"],\n    \n    "Alternative Digital Currency": ["BRICS Currency", "BRICS", "Bictoin", "BCT"]\n}\n</themed_dictionary>\n\nI\'ve focused on creating specific themes that group closely related tokens while avoiding overly broad categories. Each group contains tokens that share unique characteristics or references. I\'ve excluded many tokens that didn\'t fit into clear, specific themes rather than forcing them into broader, less meaningful categories.\n</ideal_output>\n</example>\n</examples>\n\n',
                        },
                        {
                            "type": "text",
                            "text": 'You will be given a list of token names and symbols. Your task is to identify specific themes among these tokens and group them accordingly. Here is the list of tokens:\n\n<token_list>\n{{TOKEN_LIST}}\n</token_list>\n\nYour goal is to create a dictionary where the keys are themes and the values are lists of tokens that fit those themes. Follow these guidelines:\n\n1. Themes should be as specific as possible, not broad categories.\n2. Each theme should contain only a few items (typically 2-4).\n3. Not every token needs to be categorized if it doesn\'t fit a specific theme.\n4. Focus on unique or niche themes that accurately represent the grouped tokens.\n\nAvoid overly broad themes such as "internet meme," "finance," "artificial intelligence," or "animals." Instead, aim for more specific themes like "space exploration cryptocurrencies," "food-based meme tokens," or "blockchain gaming assets."\n\nExamples of good themes:\n- "Canine-inspired meme tokens"\n- "Decentralized file storage projects"\n- "Metaverse real estate tokens"\n\nExamples of bad (too broad) themes:\n- "Cryptocurrency"\n- "Technology"\n- "Entertainment"\n\nThink carefully about the connections between the tokens and identify the most specific themes possible. Then, provide your themed dictionary output in the following format:\n\n<themed_dictionary>\n{\n    "Theme 1": ["Token1", "Token2", "Token3"],\n    "Theme 2": ["Token4", "Token5"],\n    "Theme 3": ["Token6", "Token7", "Token8"]\n}\n</themed_dictionary>\n\nEnsure that your themes are specific and that each group contains only a few closely related tokens.'.replace(
                                "{{TOKEN_LIST}}", token_list
                            ),
                        },
                    ],
                }
            ],
        )

        content = message.content[0].text

        # Extract dictionary string between <themed_dictionary> tags
        start_idx = content.find("<themed_dictionary>") + len("<themed_dictionary>")
        end_idx = content.find("</themed_dictionary>")
        dict_str = content[start_idx:end_idx].strip()

        # Convert string to actual dictionary using eval()
        # Note: eval() is safe here since we control the input from Claude
        themed_dict = eval(dict_str)

        print("all themes: ", themed_dict)

        # Sort the themes by the length of their values in descending order
        sorted_themes = sorted(themed_dict.items(), key=lambda item: len(item[1]), reverse=True)

        # Save the sorted themes to the database
        self.db_manager.save_themes(dict(sorted_themes))

        # Select the top x themes
        top_themes = dict(sorted_themes[:top_x])

        print("top themes: ", top_themes)

        return top_themes
