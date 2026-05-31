from tools.tools import GenerateStory, SelectName, SelectPlot, SelectSetting

TOOLS = {
    "SelectName": SelectName,
    "SelectSetting": SelectSetting,
    "SelectPlot": SelectPlot,
    "GenerateStory": GenerateStory,
}

TOOL_DESCRIPTIONS = {
    "SelectName": "Select a random name from the fantasy names list. args: none",
    "SelectSetting": "Select a random setting from the settings list. args: none",
    "SelectPlot": "Select a random plot from the plot list. args: none",
    "GenerateStory": "Generate a story. args: none",
}
