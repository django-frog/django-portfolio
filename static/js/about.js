import { navbar } from './base.js';

export async function load_github_data(github_url){
    const followingPlaceholder = document.getElementById('following_placeholder');
    const followingContent = document.getElementById('n_following');

    const followersPlaceholder = document.getElementById('followers_placeholder');
    const followersContent = document.getElementById('n_followers');

    const githubImgPlaceholder = document.getElementById('github_img_placeholder');
    const githubImgContent = document.getElementById('github_img');
    
    const githubNamePlaceholder = document.getElementById('github_name_placeholder');
    const githubNameContent = document.getElementById('github_name');

    const response = await fetch(github_url);
    const github_data = await response.json();

    followingPlaceholder.classList.add('hidden'); // Hide the placeholder
    followingContent.classList.remove('hidden'); // Show the actual data
    followingContent.innerHTML = github_data.following

    followersPlaceholder.classList.add('hidden'); // Hide the placeholder
    followersContent.classList.remove('hidden'); // Show the actual data
    followersContent.innerHTML = github_data.followers

    githubImgPlaceholder.classList.add('hidden'); // Hide the placeholder
    githubImgContent.classList.remove('hidden'); // Show the actual data
    githubImgContent.src = github_data.avatar_url;

    githubNamePlaceholder.classList.add('hidden'); // Hide the placeholder
    githubNameContent.classList.remove('hidden'); // Show the actual data
    githubNameContent.innerHTML = github_data.login
}